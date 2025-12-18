package com.omniagent.sdk.model;

import java.util.List;

/**
 * 多模态响应
 */
public class MultiModalResponse {
    
    private final String sessionId;
    private final List<MultiModalOutput> outputs;
    private final ProcessingMetadata metadata;
    
    public MultiModalResponse(String sessionId, List<MultiModalOutput> outputs, ProcessingMetadata metadata) {
        this.sessionId = sessionId;
        this.outputs = outputs;
        this.metadata = metadata;
    }
    
    public String getSessionId() { return sessionId; }
    public List<MultiModalOutput> getOutputs() { return outputs; }
    public ProcessingMetadata getMetadata() { return metadata; }
    
    /**
     * 获取文本输出（便捷方法）
     */
    public String getTextContent() {
        if (outputs == null || outputs.isEmpty()) return "";
        for (MultiModalOutput output : outputs) {
            if (output.hasText()) {
                return output.getText().getContent();
            }
        }
        return "";
    }
    
    // 输出类
    public static class MultiModalOutput {
        private TextOutput text;
        private AudioOutput audio;
        
        public MultiModalOutput() {}
        
        public static MultiModalOutput ofText(String content, String role) {
            MultiModalOutput output = new MultiModalOutput();
            output.text = new TextOutput(content, role);
            return output;
        }
        
        public boolean hasText() { return text != null; }
        public boolean hasAudio() { return audio != null; }
        
        public TextOutput getText() { return text; }
        public AudioOutput getAudio() { return audio; }
        
        public void setText(TextOutput text) { this.text = text; }
        public void setAudio(AudioOutput audio) { this.audio = audio; }
    }
    
    public static class TextOutput {
        private final String content;
        private final String role;
        
        public TextOutput(String content, String role) {
            this.content = content;
            this.role = role;
        }
        
        public String getContent() { return content; }
        public String getRole() { return role; }
    }
    
    public static class AudioOutput {
        private final byte[] data;
        private final String format;
        private final int sampleRate;
        
        public AudioOutput(byte[] data, String format, int sampleRate) {
            this.data = data;
            this.format = format;
            this.sampleRate = sampleRate;
        }
        
        public byte[] getData() { return data; }
        public String getFormat() { return format; }
        public int getSampleRate() { return sampleRate; }
    }
    
    // 元数据
    public static class ProcessingMetadata {
        private String finishReason;
        private int promptTokens;
        private int completionTokens;
        private int audioDurationMs;
        private String transcribedText;
        private long latencyMs;
        
        public String getFinishReason() { return finishReason; }
        public int getPromptTokens() { return promptTokens; }
        public int getCompletionTokens() { return completionTokens; }
        public int getAudioDurationMs() { return audioDurationMs; }
        public String getTranscribedText() { return transcribedText; }
        public long getLatencyMs() { return latencyMs; }
        
        public void setFinishReason(String finishReason) { this.finishReason = finishReason; }
        public void setPromptTokens(int promptTokens) { this.promptTokens = promptTokens; }
        public void setCompletionTokens(int completionTokens) { this.completionTokens = completionTokens; }
        public void setAudioDurationMs(int audioDurationMs) { this.audioDurationMs = audioDurationMs; }
        public void setTranscribedText(String transcribedText) { this.transcribedText = transcribedText; }
        public void setLatencyMs(long latencyMs) { this.latencyMs = latencyMs; }
    }
}
