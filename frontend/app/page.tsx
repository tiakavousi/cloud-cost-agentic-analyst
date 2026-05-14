"use client";

import React, { useState, useEffect, useRef } from "react";
import { Input, Button, Upload, message, Typography, Avatar, Spin } from "antd";
import { UploadOutlined, SendOutlined, UserOutlined, RobotOutlined } from "@ant-design/icons";
import type { UploadProps } from "antd";

const { Title, Text } = Typography;

// Define our message structure
interface ChatMessage {
  role: "user" | "bot";
  text: string;
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState("");
  
  // Auto-scroll reference
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate a random session ID on first load
  useEffect(() => {
    setSessionId(Math.random().toString(36).substring(7));
    setMessages([
      { role: "bot", text: "Hello! Please upload your document (PDF) and ask me anything." }
    ]);
  }, []);

  // Auto-scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Handle PDF Upload to FastAPI
  const uploadProps: UploadProps = {
    name: "file",
    action: `${process.env.NEXT_PUBLIC_API_URL}/upload-pdf/`,
    onChange(info) {
      if (info.file.status === "uploading") {
        setIsLoading(true);
      }
      if (info.file.status === "done") {
        setIsLoading(false);
        message.success(`${info.file.name} successfully processed into vector database!`);
      } else if (info.file.status === "error") {
        setIsLoading(false);
        message.error(`${info.file.name} file upload failed.`);
      }
    },
    showUploadList: false,
  };

  // Handle sending a chat message
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage = inputValue.trim();
    setInputValue(""); // Clear input box immediately
    setMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage,
          session_id: sessionId,
        }),
      });

      if (!response.ok) throw new Error("Failed to get response from server");

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "bot", text: data.answer }]);
    } catch (error) {
      message.error("Error communicating with the Assistant.");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center justify-between min-h-screen bg-gray-50 p-4 md:p-8">
      {/* Header Container */}
      <div className="w-full max-w-3xl flex justify-between items-center mb-6 bg-white p-4 rounded-xl shadow-sm border border-gray-100">
        <Title level={4} style={{ margin: 0 }} className="text-gray-800">
          🩺 Assistant
        </Title>
        <Upload {...uploadProps} accept=".pdf">
          <Button icon={<UploadOutlined />} type="default">
            Upload PDF
          </Button>
        </Upload>
      </div>

      {/* Chat History Container */}
      <div className="w-full max-w-3xl flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              <Avatar
                icon={msg.role === "user" ? <UserOutlined /> : <RobotOutlined />}
                className={msg.role === "user" ? "bg-blue-500" : "bg-emerald-500"}
              />
              <div
                className={`max-w-[75%] p-4 rounded-2xl shadow-sm text-sm ${
                  msg.role === "user"
                    ? "bg-blue-50 text-blue-900 rounded-tr-none border border-blue-100"
                    : "bg-gray-50 text-gray-800 rounded-tl-none border border-gray-200"
                }`}
              >
                {/* Simple formatting to handle newlines from the LLM */}
                {msg.text.split('\n').map((line, i) => (
                  <React.Fragment key={i}>
                    {line}
                    <br />
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}
          
          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-4">
              <Avatar icon={<RobotOutlined />} className="bg-emerald-500" />
              <div className="p-4 bg-gray-50 rounded-2xl rounded-tl-none border border-gray-200 shadow-sm flex items-center justify-center">
                <Spin size="small" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-gray-50 border-t border-gray-200 flex gap-2">
          <Input
            size="large"
            placeholder="Ask about your documents..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleSendMessage}
            disabled={isLoading}
            className="flex-1 rounded-lg"
          />
          <Button
            size="large"
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isLoading}
            className="bg-blue-600 rounded-lg px-6"
          >
            Send
          </Button>
        </div>
      </div>
    </main>
  );
}