import React, { useState, useEffect } from 'react';
import { Play, Save, Settings, FileCode } from 'lucide-react';

const CodeEditor = () => {
    const [files, setFiles] = useState([]);
    const [activeFile, setActiveFile] = useState(null);
    const [code, setCode] = useState('');
    const [status, setStatus] = useState('Ready');

    // Load file list
    useEffect(() => {
        fetch('http://localhost:8000/files')
            .then(res => res.json())
            .then(data => {
                setFiles(data.files);
                if (data.files.length > 0) {
                    // Prefer main.py or first file
                    const defaultFile = data.files.includes('main.py') ? 'main.py' : data.files[0];
                    setActiveFile(defaultFile);
                }
            })
            .catch(err => setStatus('Error loading files'));
    }, []);

    // Load file content
    useEffect(() => {
        if (!activeFile) return;

        setStatus('Loading...');
        fetch(`http://localhost:8000/files/${activeFile}`)
            .then(res => res.json())
            .then(data => {
                setCode(data.content);
                setStatus('Ready');
            })
            .catch(err => setStatus('Error loading content'));
    }, [activeFile]);

    const handleSave = () => {
        if (!activeFile) return;

        setStatus('Saving...');
        fetch(`http://localhost:8000/files/${activeFile}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: code })
        })
            .then(res => res.json())
            .then(() => setStatus('Saved'))
            .catch(() => setStatus('Error saving'));

        setTimeout(() => setStatus('Ready'), 2000);
    };

    return (
        <div className="flex flex-col h-full bg-[#1e1e1e] rounded-xl overflow-hidden border border-white/10 shadow-2xl">
            {/* Editor Toolbar */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#252526] border-b border-white/5">
                <div className="flex items-center space-x-2">
                    <div className="flex space-x-1 mr-4">
                        <div className="w-3 h-3 rounded-full bg-red-500" />
                        <div className="w-3 h-3 rounded-full bg-yellow-500" />
                        <div className="w-3 h-3 rounded-full bg-green-500" />
                    </div>

                    {/* File Selector */}
                    <div className="flex items-center">
                        <FileCode size={14} className="text-blue-400 mr-2" />
                        <select
                            value={activeFile || ''}
                            onChange={(e) => setActiveFile(e.target.value)}
                            className="bg-transparent text-xs text-gray-300 font-mono focus:outline-none cursor-pointer hover:text-white"
                        >
                            {files.map(f => <option key={f} value={f}>{f}</option>)}
                        </select>
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <button
                        onClick={handleSave}
                        className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
                        title="Save (Ctrl+S)"
                    >
                        <Save size={14} />
                    </button>
                    <button className="flex items-center px-3 py-1 bg-green-600 hover:bg-green-500 text-white text-xs rounded transition-colors opacity-50 cursor-not-allowed" title="Run not implemented yet">
                        <Play size={12} className="mr-1" />
                        Run
                    </button>
                </div>
            </div>

            {/* Editor Content */}
            <div className="flex-1 relative font-mono text-sm">
                <textarea
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="w-full h-full bg-[#1e1e1e] text-gray-300 p-4 resize-none focus:outline-none"
                    spellCheck="false"
                />
            </div>

            {/* Status Bar */}
            <div className="px-4 py-1 bg-primary/20 text-blue-200 text-[10px] flex justify-between items-center">
                <span>{activeFile ? activeFile : 'No file selected'}</span>
                <span>{status}</span>
            </div>
        </div>
    );
};

export default CodeEditor;
