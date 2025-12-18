package com.omniagent.sdk.model;

import lombok.Builder;
import lombok.Data;

/**
 * 会话配置
 */
@Data
@Builder
public class SessionConfig {
    @Builder.Default
    private String model = "qwen-turbo";
    
    @Builder.Default
    private float temperature = 0.7f;
    
    @Builder.Default
    private int maxTokens = 2048;
    
    private String systemPrompt;
    
    @Builder.Default
    private String sttModel = "paraformer-realtime-v2";
    
    @Builder.Default
    private String language = "zh-CN";
    
    @Builder.Default
    private int sampleRate = 16000;
    
    public OmniAgentProto.SessionConfig toProto() {
        OmniAgentProto.LlmConfig.Builder llmBuilder = OmniAgentProto.LlmConfig.newBuilder()
            .setModel(model)
            .setTemperature(temperature)
            .setMaxTokens(maxTokens);
        
        if (systemPrompt != null) {
            llmBuilder.setSystemPrompt(systemPrompt);
        }
        
        return OmniAgentProto.SessionConfig.newBuilder()
            .setLlm(llmBuilder.build())
            .setStt(OmniAgentProto.SttConfig.newBuilder()
                .setModel(sttModel)
                .setLanguage(language)
                .setSampleRate(sampleRate)
                .build())
            .build();
    }
}
