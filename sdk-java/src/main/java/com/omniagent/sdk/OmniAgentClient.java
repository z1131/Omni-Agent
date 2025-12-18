package com.omniagent.sdk;

import com.omniagent.sdk.exception.*;
import com.omniagent.sdk.model.*;
import io.grpc.*;
import io.grpc.stub.StreamObserver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Iterator;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

/**
 * Omni-Agent Java SDK 客户端
 * 
 * <pre>{@code
 * // 创建客户端
 * OmniAgentClient client = OmniAgentClient.builder()
 *     .target("localhost:50051")
 *     .build();
 * 
 * // 创建会话
 * Session session = client.createSession(SessionConfig.builder()
 *     .model("qwen-plus")
 *     .systemPrompt("你是专业助手")
 *     .build());
 * 
 * // 对话
 * String response = session.chat("你好");
 * 
 * // 流式对话
 * session.chatStream("讲个故事", chunk -> System.out.print(chunk));
 * 
 * // 关闭
 * session.close();
 * client.shutdown();
 * }</pre>
 */
public class OmniAgentClient implements AutoCloseable {
    
    private static final Logger log = LoggerFactory.getLogger(OmniAgentClient.class);
    
    private final ManagedChannel channel;
    private final OmniAgentGrpc.OmniAgentBlockingStub blockingStub;
    private final OmniAgentGrpc.OmniAgentStub asyncStub;
    
    private OmniAgentClient(Builder builder) {
        ManagedChannelBuilder<?> channelBuilder = ManagedChannelBuilder
            .forTarget(builder.target)
            .maxInboundMessageSize(50 * 1024 * 1024);
        
        if (!builder.useTls) {
            channelBuilder.usePlaintext();
        }
        
        this.channel = channelBuilder.build();
        this.blockingStub = OmniAgentGrpc.newBlockingStub(channel);
        this.asyncStub = OmniAgentGrpc.newStub(channel);
        
        log.info("OmniAgentClient created, target: {}", builder.target);
    }
    
    public static Builder builder() {
        return new Builder();
    }
    
    // ========== 会话管理 ==========
    
    /**
     * 创建会话
     */
    public Session createSession(SessionConfig config) {
        try {
            OmniAgentProto.CreateSessionRequest request = OmniAgentProto.CreateSessionRequest.newBuilder()
                .setConfig(config.toProto())
                .build();
            
            OmniAgentProto.CreateSessionResponse response = blockingStub.createSession(request);
            
            log.debug("Session created: {}", response.getSessionId());
            
            return new Session(response.getSessionId(), this, config);
            
        } catch (StatusRuntimeException e) {
            throw convertGrpcError(e);
        }
    }
    
    /**
     * 创建默认会话
     */
    public Session createSession() {
        return createSession(SessionConfig.builder().build());
    }
    
    /**
     * 获取已有会话
     */
    public Session getSession(String sessionId) {
        try {
            OmniAgentProto.GetSessionRequest request = OmniAgentProto.GetSessionRequest.newBuilder()
                .setSessionId(sessionId)
                .build();
            
            OmniAgentProto.GetSessionResponse response = blockingStub.getSession(request);
            
            return new Session(response.getSessionId(), this, null);
            
        } catch (StatusRuntimeException e) {
            throw convertGrpcError(e);
        }
    }
    
    /**
     * 关闭会话
     */
    public boolean closeSession(String sessionId) {
        try {
            OmniAgentProto.CloseSessionRequest request = OmniAgentProto.CloseSessionRequest.newBuilder()
                .setSessionId(sessionId)
                .build();
            
            OmniAgentProto.CloseSessionResponse response = blockingStub.closeSession(request);
            
            return response.getSuccess();
            
        } catch (StatusRuntimeException e) {
            throw convertGrpcError(e);
        }
    }
    
    // ========== Chat ==========
    
    /**
     * 非流式对话
     */
    public ChatResponse chat(String sessionId, List<Message> messages) {
        try {
            OmniAgentProto.ChatRequest.Builder requestBuilder = OmniAgentProto.ChatRequest.newBuilder()
                .setSessionId(sessionId);
            
            for (Message msg : messages) {
                requestBuilder.addMessages(msg.toProto());
            }
            
            OmniAgentProto.ChatResponse response = blockingStub.chat(requestBuilder.build());
            
            return ChatResponse.fromProto(response);
            
        } catch (StatusRuntimeException e) {
            throw convertGrpcError(e);
        }
    }
    
    /**
     * 流式对话
     */
    public void chatStream(String sessionId, List<Message> messages, Consumer<String> onChunk) {
        chatStream(sessionId, messages, onChunk, null, null);
    }
    
    /**
     * 流式对话（带回调）
     */
    public void chatStream(String sessionId, List<Message> messages, 
                          Consumer<String> onChunk,
                          Consumer<String> onComplete,
                          Consumer<Throwable> onError) {
        try {
            OmniAgentProto.ChatRequest.Builder requestBuilder = OmniAgentProto.ChatRequest.newBuilder()
                .setSessionId(sessionId);
            
            for (Message msg : messages) {
                requestBuilder.addMessages(msg.toProto());
            }
            
            Iterator<OmniAgentProto.ChatStreamResponse> responseIterator = 
                blockingStub.chatStream(requestBuilder.build());
            
            StringBuilder fullContent = new StringBuilder();
            
            while (responseIterator.hasNext()) {
                OmniAgentProto.ChatStreamResponse chunk = responseIterator.next();
                if (!chunk.getDelta().isEmpty()) {
                    fullContent.append(chunk.getDelta());
                    if (onChunk != null) {
                        onChunk.accept(chunk.getDelta());
                    }
                }
                if (!chunk.getFinishReason().isEmpty() && onComplete != null) {
                    onComplete.accept(fullContent.toString());
                }
            }
            
        } catch (StatusRuntimeException e) {
            if (onError != null) {
                onError.accept(convertGrpcError(e));
            } else {
                throw convertGrpcError(e);
            }
        }
    }
    
    // ========== 统一多模态接口 ==========
    
    /**
     * 统一多模态处理（非流式）
     * 
     * @param sessionId 会话ID
     * @param inputs 多模态输入列表
     * @param config 处理配置
     * @return 多模态响应
     */
    public MultiModalResponse process(String sessionId, List<MultiModalInput> inputs, ProcessingConfig config) {
        try {
            OmniAgentProto.MultiModalRequest.Builder requestBuilder = OmniAgentProto.MultiModalRequest.newBuilder()
                .setSessionId(sessionId);
            
            // 添加输入
            for (MultiModalInput input : inputs) {
                OmniAgentProto.ModalityInput.Builder inputBuilder = OmniAgentProto.ModalityInput.newBuilder();
                
                if (input.hasText()) {
                    inputBuilder.setText(OmniAgentProto.TextInput.newBuilder()
                        .setContent(input.getText().getContent())
                        .setRole(input.getText().getRole())
                        .build());
                } else if (input.hasAudio()) {
                    inputBuilder.setAudio(OmniAgentProto.AudioInput.newBuilder()
                        .setData(com.google.protobuf.ByteString.copyFrom(input.getAudio().getData()))
                        .setFormat(input.getAudio().getFormat())
                        .setSampleRate(input.getAudio().getSampleRate())
                        .build());
                } else if (input.hasImage()) {
                    inputBuilder.setImage(OmniAgentProto.ImageInput.newBuilder()
                        .setData(com.google.protobuf.ByteString.copyFrom(input.getImage().getData()))
                        .setFormat(input.getImage().getFormat())
                        .setPrompt(input.getImage().getPrompt() != null ? input.getImage().getPrompt() : "")
                        .build());
                }
                
                requestBuilder.addInputs(inputBuilder.build());
            }
            
            // 添加配置
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
                requestBuilder.setConfig(configBuilder.build());
            }
            
            OmniAgentProto.MultiModalResponse response = blockingStub.process(requestBuilder.build());
            
            return convertMultiModalResponse(response);
            
        } catch (StatusRuntimeException e) {
            throw convertGrpcError(e);
        }
    }
    
    /**
     * 统一多模态处理（简化版）
     */
    public MultiModalResponse process(String sessionId, List<MultiModalInput> inputs) {
        return process(sessionId, inputs, ProcessingConfig.builder().build());
    }
    
    /**
     * 统一多模态处理（单输入）
     */
    public MultiModalResponse process(String sessionId, MultiModalInput input, ProcessingConfig config) {
        return process(sessionId, List.of(input), config);
    }
    
    /**
     * 统一多模态处理（单文本输入）
     */
    public String processText(String sessionId, String text, ProcessingConfig config) {
        MultiModalResponse response = process(sessionId, MultiModalInput.ofText(text), config);
        return response.getTextContent();
    }
    
    /**
     * 统一多模态处理（单音频输入）
     */
    public String processAudio(String sessionId, byte[] audioData, ProcessingConfig config) {
        MultiModalResponse response = process(sessionId, MultiModalInput.ofAudio(audioData), config);
        return response.getTextContent();
    }
    
    /**
     * 流式多模态处理
     * 
     * @param sessionId 会话ID
     * @param config 处理配置
     * @param initialInputs 初始输入（文本/图片，非流式部分）
     * @param onStt STT 中间结果回调
     * @param onLlm LLM 增量输出回调
     * @param onComplete 完成回调
     * @param onError 错误回调
     * @return 流式处理流对象
     */
    public MultiModalStream processStream(
            String sessionId,
            ProcessingConfig config,
            List<MultiModalInput> initialInputs,
            Consumer<String> onStt,
            Consumer<String> onLlm,
            Runnable onComplete,
            Consumer<Throwable> onError) {
        
        StreamObserver<OmniAgentProto.MultiModalStreamResponse> responseObserver = new StreamObserver<>() {
            @Override
            public void onNext(OmniAgentProto.MultiModalStreamResponse response) {
                if (response.hasReady()) {
                    log.debug("ProcessStream ready: {}", response.getReady().getSessionId());
                } else if (response.hasStt()) {
                    if (onStt != null) {
                        onStt.accept(response.getStt().getText());
                    }
                } else if (response.hasLlm()) {
                    if (onLlm != null) {
                        onLlm.accept(response.getLlm().getDelta());
                    }
                } else if (response.hasComplete()) {
                    log.debug("ProcessStream complete: {}", response.getComplete().getFinishReason());
                    if (onComplete != null) {
                        onComplete.run();
                    }
                } else if (response.hasError()) {
                    if (onError != null) {
                        onError.accept(new OmniAgentException(response.getError().getMessage()));
                    }
                }
            }
            
            @Override
            public void onError(Throwable t) {
                if (onError != null) {
                    onError.accept(t);
                }
            }
            
            @Override
            public void onCompleted() {
                // 服务端完成
            }
        };
        
        StreamObserver<OmniAgentProto.MultiModalStreamRequest> requestObserver = 
            asyncStub.processStream(responseObserver);
        
        MultiModalStream stream = new MultiModalStream(requestObserver, sessionId);
        
        // 发送开始帧
        stream.sendStartFrame(config, initialInputs);
        
        return stream;
    }
    
    /**
     * 流式多模态处理（简化版）
     */
    public MultiModalStream processStream(
            String sessionId,
            ProcessingConfig config,
            Consumer<String> onStt,
            Consumer<String> onLlm,
            Runnable onComplete,
            Consumer<Throwable> onError) {
        return processStream(sessionId, config, null, onStt, onLlm, onComplete, onError);
    }
    
    private MultiModalResponse convertMultiModalResponse(OmniAgentProto.MultiModalResponse proto) {
        List<MultiModalResponse.MultiModalOutput> outputs = new java.util.ArrayList<>();
        
        for (OmniAgentProto.ModalityOutput output : proto.getOutputsList()) {
            MultiModalResponse.MultiModalOutput mmOutput = new MultiModalResponse.MultiModalOutput();
            if (output.hasText()) {
                mmOutput.setText(new MultiModalResponse.TextOutput(
                    output.getText().getContent(),
                    output.getText().getRole()
                ));
            }
            if (output.hasAudio()) {
                mmOutput.setAudio(new MultiModalResponse.AudioOutput(
                    output.getAudio().getData().toByteArray(),
                    output.getAudio().getFormat(),
                    output.getAudio().getSampleRate()
                ));
            }
            outputs.add(mmOutput);
        }
        
        MultiModalResponse.ProcessingMetadata metadata = new MultiModalResponse.ProcessingMetadata();
        if (proto.hasMetadata()) {
            metadata.setFinishReason(proto.getMetadata().getFinishReason());
            metadata.setPromptTokens(proto.getMetadata().getPromptTokens());
            metadata.setCompletionTokens(proto.getMetadata().getCompletionTokens());
            metadata.setAudioDurationMs(proto.getMetadata().getAudioDurationMs());
            metadata.setTranscribedText(proto.getMetadata().getTranscribedText());
            metadata.setLatencyMs(proto.getMetadata().getLatencyMs());
        }
        
        return new MultiModalResponse(proto.getSessionId(), outputs, metadata);
    }
    
    // ========== STT ==========
    
    /**
     * 单次语音识别
     */
    public String transcribe(String sessionId, byte[] audioData) {
        try {
            OmniAgentProto.TranscribeRequest request = OmniAgentProto.TranscribeRequest.newBuilder()
                .setSessionId(sessionId)
                .setAudioData(com.google.protobuf.ByteString.copyFrom(audioData))
                .build();
            
            OmniAgentProto.TranscribeResponse response = blockingStub.transcribe(request);
            
            return response.getText();
            
        } catch (StatusRuntimeException e) {
            throw convertGrpcError(e);
        }
    }
    
    /**
     * 流式语音识别
     */
    public StreamObserver<byte[]> streamStt(String sessionId,
                                            Consumer<SttResult> onResult,
                                            Consumer<Throwable> onError,
                                            Runnable onComplete) {
        
        StreamObserver<OmniAgentProto.SttResponse> responseObserver = new StreamObserver<>() {
            @Override
            public void onNext(OmniAgentProto.SttResponse response) {
                if (response.hasResult()) {
                    SttResult result = SttResult.fromProto(response.getResult());
                    onResult.accept(result);
                } else if (response.hasError()) {
                    onError.accept(new SttException(response.getError().getMessage()));
                }
            }
            
            @Override
            public void onError(Throwable t) {
                onError.accept(t);
            }
            
            @Override
            public void onCompleted() {
                if (onComplete != null) {
                    onComplete.run();
                }
            }
        };
        
        StreamObserver<OmniAgentProto.SttRequest> requestObserver = asyncStub.streamSTT(responseObserver);
        
        // 发送初始化请求
        requestObserver.onNext(OmniAgentProto.SttRequest.newBuilder()
            .setInit(OmniAgentProto.SttInitRequest.newBuilder()
                .setSessionId(sessionId)
                .build())
            .build());
        
        // 返回封装的 observer
        return new StreamObserver<>() {
            @Override
            public void onNext(byte[] audioData) {
                requestObserver.onNext(OmniAgentProto.SttRequest.newBuilder()
                    .setAudioData(com.google.protobuf.ByteString.copyFrom(audioData))
                    .build());
            }
            
            @Override
            public void onError(Throwable t) {
                requestObserver.onError(t);
            }
            
            @Override
            public void onCompleted() {
                requestObserver.onCompleted();
            }
        };
    }
    
    // ========== 生命周期 ==========
    
    /**
     * 关闭客户端
     */
    public void shutdown() {
        try {
            channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
            log.info("OmniAgentClient shutdown");
        } catch (InterruptedException e) {
            channel.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
    
    @Override
    public void close() {
        shutdown();
    }
    
    // ========== 工具方法 ==========
    
    private OmniAgentException convertGrpcError(StatusRuntimeException e) {
        Status status = e.getStatus();
        String description = status.getDescription();
        
        return switch (status.getCode()) {
            case UNAVAILABLE -> new ConnectionException("Service unavailable: " + description);
            case NOT_FOUND -> new SessionNotFoundException(description != null ? description : "unknown");
            case DEADLINE_EXCEEDED -> new TimeoutException("Request timeout");
            case INVALID_ARGUMENT -> new InvalidParamException("unknown", description);
            default -> new OmniAgentException("gRPC error: " + status.getCode() + " - " + description);
        };
    }
    
    // ========== Builder ==========
    
    public static class Builder {
        private String target = "localhost:50051";
        private boolean useTls = false;
        
        public Builder target(String target) {
            this.target = target;
            return this;
        }
        
        public Builder useTls(boolean useTls) {
            this.useTls = useTls;
            return this;
        }
        
        public OmniAgentClient build() {
            return new OmniAgentClient(this);
        }
    }
}
