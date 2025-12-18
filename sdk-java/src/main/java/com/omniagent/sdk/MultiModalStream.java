package com.omniagent.sdk;

import com.omniagent.sdk.model.MultiModalInput;
import com.omniagent.sdk.model.ProcessingConfig;
import io.grpc.stub.StreamObserver;

import java.util.List;
import java.util.function.Consumer;

/**
 * 流式多模态处理流
 * 
 * 使用示例：
 * <pre>{@code
 * MultiModalStream stream = client.processStream(sessionId, config,
 *     stt -> System.out.println("STT: " + stt),
 *     llm -> System.out.print(llm),
 *     () -> System.out.println("\nDone"),
 *     err -> err.printStackTrace()
 * );
 * 
 * // 发送初始文本
 * stream.addText("请根据我接下来说的话回答问题");
 * 
 * // 发送音频
 * stream.sendAudio(audioChunk1);
 * stream.sendAudio(audioChunk2);
 * 
 * // 结束音频，开始生成回复
 * stream.endAudio();
 * }</pre>
 */
public class MultiModalStream implements AutoCloseable {
    
    private final StreamObserver<OmniAgentProto.MultiModalStreamRequest> requestObserver;
    private final String sessionId;
    private volatile boolean started = false;
    private volatile boolean closed = false;
    
    MultiModalStream(
        StreamObserver<OmniAgentProto.MultiModalStreamRequest> requestObserver,
        String sessionId
    ) {
        this.requestObserver = requestObserver;
        this.sessionId = sessionId;
    }
    
    /**
     * 发送开始帧（内部调用）
     */
    void sendStartFrame(ProcessingConfig config, List<MultiModalInput> initialInputs) {
        if (started) return;
        
        OmniAgentProto.StreamStartFrame.Builder startBuilder = OmniAgentProto.StreamStartFrame.newBuilder()
            .setSessionId(sessionId);
        
        // 配置
        if (config != null) {
            OmniAgentProto.ProcessingConfig.Builder configBuilder = OmniAgentProto.ProcessingConfig.newBuilder();
            if (config.getSttProvider() != null) configBuilder.setSttProvider(config.getSttProvider());
            if (config.getSttModel() != null) configBuilder.setSttModel(config.getSttModel());
            if (config.getLanguage() != null) configBuilder.setLanguage(config.getLanguage());
            if (config.getLlmProvider() != null) configBuilder.setLlmProvider(config.getLlmProvider());
            if (config.getLlmModel() != null) configBuilder.setLlmModel(config.getLlmModel());
            configBuilder.setTemperature(config.getTemperature());
            configBuilder.setMaxTokens(config.getMaxTokens());
            if (config.getSystemPrompt() != null) configBuilder.setSystemPrompt(config.getSystemPrompt());
            startBuilder.setConfig(configBuilder.build());
        }
        
        // 初始输入
        if (initialInputs != null) {
            for (MultiModalInput input : initialInputs) {
                OmniAgentProto.ModalityInput.Builder inputBuilder = OmniAgentProto.ModalityInput.newBuilder();
                if (input.hasText()) {
                    inputBuilder.setText(OmniAgentProto.TextInput.newBuilder()
                        .setContent(input.getText().getContent())
                        .setRole(input.getText().getRole())
                        .build());
                }
                startBuilder.addInitialInputs(inputBuilder.build());
            }
        }
        
        requestObserver.onNext(OmniAgentProto.MultiModalStreamRequest.newBuilder()
            .setStart(startBuilder.build())
            .build());
        
        started = true;
    }
    
    /**
     * 发送音频数据
     */
    public void sendAudio(byte[] audioData) {
        if (closed) return;
        
        requestObserver.onNext(OmniAgentProto.MultiModalStreamRequest.newBuilder()
            .setAudio(OmniAgentProto.StreamAudioFrame.newBuilder()
                .setData(com.google.protobuf.ByteString.copyFrom(audioData))
                .build())
            .build());
    }
    
    /**
     * 刷新音频缓冲
     */
    public void flush() {
        if (closed) return;
        
        requestObserver.onNext(OmniAgentProto.MultiModalStreamRequest.newBuilder()
            .setControl(OmniAgentProto.StreamControlFrame.newBuilder()
                .setCommand(OmniAgentProto.StreamControlFrame.Command.FLUSH)
                .build())
            .build());
    }
    
    /**
     * 结束音频输入，开始生成回复
     */
    public void endAudio() {
        if (closed) return;
        
        requestObserver.onNext(OmniAgentProto.MultiModalStreamRequest.newBuilder()
            .setControl(OmniAgentProto.StreamControlFrame.newBuilder()
                .setCommand(OmniAgentProto.StreamControlFrame.Command.END_AUDIO)
                .build())
            .build());
    }
    
    /**
     * 取消处理
     */
    public void cancel() {
        if (closed) return;
        
        requestObserver.onNext(OmniAgentProto.MultiModalStreamRequest.newBuilder()
            .setControl(OmniAgentProto.StreamControlFrame.newBuilder()
                .setCommand(OmniAgentProto.StreamControlFrame.Command.CANCEL)
                .build())
            .build());
        
        close();
    }
    
    @Override
    public void close() {
        if (closed) return;
        closed = true;
        
        try {
            requestObserver.onCompleted();
        } catch (Exception e) {
            // ignore
        }
    }
    
    public String getSessionId() {
        return sessionId;
    }
    
    public boolean isClosed() {
        return closed;
    }
}
