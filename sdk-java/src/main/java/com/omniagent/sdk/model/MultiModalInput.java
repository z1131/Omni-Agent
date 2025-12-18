package com.omniagent.sdk.model;

/**
 * 多模态输入
 */
public class MultiModalInput {
    
    private TextInput text;
    private AudioInput audio;
    private ImageInput image;
    
    private MultiModalInput() {}
    
    public static MultiModalInput ofText(String content) {
        return ofText(content, "user");
    }
    
    public static MultiModalInput ofText(String content, String role) {
        MultiModalInput input = new MultiModalInput();
        input.text = new TextInput(content, role);
        return input;
    }
    
    public static MultiModalInput ofAudio(byte[] data) {
        return ofAudio(data, "pcm", 16000);
    }
    
    public static MultiModalInput ofAudio(byte[] data, String format, int sampleRate) {
        MultiModalInput input = new MultiModalInput();
        input.audio = new AudioInput(data, format, sampleRate);
        return input;
    }
    
    public static MultiModalInput ofImage(byte[] data, String format) {
        MultiModalInput input = new MultiModalInput();
        input.image = new ImageInput(data, format, null);
        return input;
    }
    
    public static MultiModalInput ofImage(byte[] data, String format, String prompt) {
        MultiModalInput input = new MultiModalInput();
        input.image = new ImageInput(data, format, prompt);
        return input;
    }
    
    public boolean hasText() { return text != null; }
    public boolean hasAudio() { return audio != null; }
    public boolean hasImage() { return image != null; }
    
    public TextInput getText() { return text; }
    public AudioInput getAudio() { return audio; }
    public ImageInput getImage() { return image; }
    
    // 内部类
    public static class TextInput {
        private final String content;
        private final String role;
        
        public TextInput(String content, String role) {
            this.content = content;
            this.role = role;
        }
        
        public String getContent() { return content; }
        public String getRole() { return role; }
    }
    
    public static class AudioInput {
        private final byte[] data;
        private final String format;
        private final int sampleRate;
        
        public AudioInput(byte[] data, String format, int sampleRate) {
            this.data = data;
            this.format = format;
            this.sampleRate = sampleRate;
        }
        
        public byte[] getData() { return data; }
        public String getFormat() { return format; }
        public int getSampleRate() { return sampleRate; }
    }
    
    public static class ImageInput {
        private final byte[] data;
        private final String format;
        private final String prompt;
        
        public ImageInput(byte[] data, String format, String prompt) {
            this.data = data;
            this.format = format;
            this.prompt = prompt;
        }
        
        public byte[] getData() { return data; }
        public String getFormat() { return format; }
        public String getPrompt() { return prompt; }
    }
}
