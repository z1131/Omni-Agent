package com.omniagent.sdk.model;

/**
 * 处理配置
 */
public class ProcessingConfig {
    
    // STT 配置
    private String sttProvider;
    private String sttModel;
    private String language;
    
    // LLM 配置
    private String llmProvider;
    private String llmModel;
    private float temperature;
    private int maxTokens;
    private String systemPrompt;
    
    // 输出配置
    private boolean enableTts;
    private String ttsProvider;
    private String ttsVoice;
    
    private ProcessingConfig() {}
    
    public static Builder builder() {
        return new Builder();
    }
    
    // Getters
    public String getSttProvider() { return sttProvider; }
    public String getSttModel() { return sttModel; }
    public String getLanguage() { return language; }
    public String getLlmProvider() { return llmProvider; }
    public String getLlmModel() { return llmModel; }
    public float getTemperature() { return temperature; }
    public int getMaxTokens() { return maxTokens; }
    public String getSystemPrompt() { return systemPrompt; }
    public boolean isEnableTts() { return enableTts; }
    public String getTtsProvider() { return ttsProvider; }
    public String getTtsVoice() { return ttsVoice; }
    
    public static class Builder {
        private final ProcessingConfig config = new ProcessingConfig();
        
        public Builder sttProvider(String provider) {
            config.sttProvider = provider;
            return this;
        }
        
        public Builder sttModel(String model) {
            config.sttModel = model;
            return this;
        }
        
        public Builder language(String language) {
            config.language = language;
            return this;
        }
        
        public Builder llmProvider(String provider) {
            config.llmProvider = provider;
            return this;
        }
        
        public Builder llmModel(String model) {
            config.llmModel = model;
            return this;
        }
        
        public Builder temperature(float temperature) {
            config.temperature = temperature;
            return this;
        }
        
        public Builder maxTokens(int maxTokens) {
            config.maxTokens = maxTokens;
            return this;
        }
        
        public Builder systemPrompt(String systemPrompt) {
            config.systemPrompt = systemPrompt;
            return this;
        }
        
        public Builder enableTts(boolean enable) {
            config.enableTts = enable;
            return this;
        }
        
        public Builder ttsProvider(String provider) {
            config.ttsProvider = provider;
            return this;
        }
        
        public Builder ttsVoice(String voice) {
            config.ttsVoice = voice;
            return this;
        }
        
        public ProcessingConfig build() {
            // 设置默认值
            if (config.language == null) config.language = "zh-CN";
            if (config.llmModel == null) config.llmModel = "qwen-turbo";
            if (config.temperature == 0) config.temperature = 0.7f;
            if (config.maxTokens == 0) config.maxTokens = 2048;
            return config;
        }
    }
}
