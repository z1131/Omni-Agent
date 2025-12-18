package com.omniagent.sdk;

import com.omniagent.sdk.model.*;
import io.grpc.stub.StreamObserver;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.function.Consumer;

/**
 * 会话对象
 * 
 * <pre>{@code
 * Session session = client.createSession();
 * 
 * // 简单对话
 * String response = session.chat("你好");
 * 
 * // 流式对话
 * session.chatStream("讲故事", chunk -> System.out.print(chunk));
 * 
 * // 关闭
 * session.close();
 * }</pre>
 */
public class Session implements AutoCloseable {
    
    private final String sessionId;
    private final OmniAgentClient client;
    private final SessionConfig config;
    private final List<Message> messages;
    private volatile boolean closed = false;
    
    Session(String sessionId, OmniAgentClient client, SessionConfig config) {
        this.sessionId = sessionId;
        this.client = client;
        this.config = config;
        this.messages = new ArrayList<>();
    }
    
    public String getSessionId() {
        return sessionId;
    }
    
    public SessionConfig getConfig() {
        return config;
    }
    
    public List<Message> getMessages() {
        return Collections.unmodifiableList(messages);
    }
    
    public boolean isClosed() {
        return closed;
    }
    
    private void checkClosed() {
        if (closed) {
            throw new IllegalStateException("Session " + sessionId + " is closed");
        }
    }
    
    // ========== 对话 ==========
    
    /**
     * 发送消息并获取回复
     */
    public String chat(String content) {
        return chat(content, true);
    }
    
    /**
     * 发送消息并获取回复
     * 
     * @param content 消息内容
     * @param remember 是否记录到对话历史
     */
    public String chat(String content, boolean remember) {
        checkClosed();
        
        Message userMessage = Message.user(content);
        List<Message> allMessages = new ArrayList<>(messages);
        allMessages.add(userMessage);
        
        ChatResponse response = client.chat(sessionId, allMessages);
        
        if (remember) {
            messages.add(userMessage);
            messages.add(Message.assistant(response.getContent()));
        }
        
        return response.getContent();
    }
    
    /**
     * 流式对话
     */
    public void chatStream(String content, Consumer<String> onChunk) {
        chatStream(content, onChunk, true);
    }
    
    /**
     * 流式对话
     */
    public void chatStream(String content, Consumer<String> onChunk, boolean remember) {
        checkClosed();
        
        Message userMessage = Message.user(content);
        List<Message> allMessages = new ArrayList<>(messages);
        allMessages.add(userMessage);
        
        StringBuilder fullContent = new StringBuilder();
        
        client.chatStream(sessionId, allMessages, 
            chunk -> {
                fullContent.append(chunk);
                onChunk.accept(chunk);
            },
            complete -> {
                if (remember) {
                    messages.add(userMessage);
                    messages.add(Message.assistant(fullContent.toString()));
                }
            },
            null
        );
    }
    
    /**
     * 使用自定义消息列表对话
     */
    public ChatResponse chatWithMessages(List<Message> customMessages) {
        checkClosed();
        return client.chat(sessionId, customMessages);
    }
    
    // ========== STT ==========
    
    /**
     * 单次语音识别
     */
    public String transcribe(byte[] audioData) {
        checkClosed();
        return client.transcribe(sessionId, audioData);
    }
    
    /**
     * 流式语音识别
     * 
     * @return StreamObserver 用于发送音频数据
     */
    public StreamObserver<byte[]> transcribeStream(Consumer<SttResult> onResult,
                                                   Consumer<Throwable> onError,
                                                   Runnable onComplete) {
        checkClosed();
        return client.streamStt(sessionId, onResult, onError, onComplete);
    }
    
    // ========== 历史管理 ==========
    
    /**
     * 清空对话历史
     */
    public void clearHistory() {
        messages.clear();
    }
    
    /**
     * 添加消息到历史
     */
    public void addMessage(String role, String content) {
        messages.add(new Message(role, content));
    }
    
    /**
     * 设置系统提示词
     */
    public void setSystemPrompt(String prompt) {
        messages.removeIf(m -> "system".equals(m.getRole()));
        messages.add(0, Message.system(prompt));
    }
    
    // ========== 生命周期 ==========
    
    @Override
    public void close() {
        if (!closed) {
            client.closeSession(sessionId);
            closed = true;
        }
    }
    
    @Override
    public String toString() {
        String status = closed ? "closed" : "active";
        return String.format("Session(id=%s, status=%s, messages=%d)", 
            sessionId, status, messages.size());
    }
}
