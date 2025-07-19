import React, { useState, useRef, useEffect } from 'react';
import './ChatBox.css';

const ChatBox = () => {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [botThinking, setBotThinking] = useState(false);
  const [currentSuggestions, setCurrentSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);

  const typingIntervalRef = useRef(null);
  const chatboxRef = useRef(null);

  const suggestedQuestions = [
    "What are the company leave policies?",
    "How can I apply for a sick leave?",
    "Tell me about the holiday calendar.",
    "What are the working hours?",
    "How can I update my bank details?",
    "Can I work remotely?",
    "Where can I download my payslip?",
  ];

  useEffect(() => {
    const shuffled = [...suggestedQuestions].sort(() => 0.5 - Math.random());
    setCurrentSuggestions(shuffled.slice(0, 3));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setBotThinking(true);
    setQuery('');
    setCurrentSuggestions([]);

    const userMsg = { type: 'user', text: query };
    const botMsg = { type: 'bot', text: '' };

    let botIndex = -1;

    setMessages((prev) => {
      const updated = [...prev, userMsg, botMsg];
      botIndex = updated.length - 1;
      return updated;
    });

    try {
      const response = await fetch('http://172.16.13.246:3001/chat_api/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      const fullText = data.response || 'Sorry, something went wrong.';

      setTimeout(() => {
        setBotThinking(false);
        setIsTyping(true);

        let i = 0;
        typingIntervalRef.current = setInterval(() => {
          if (i >= fullText.length) {
            clearInterval(typingIntervalRef.current);
            typingIntervalRef.current = null;
            setIsTyping(false);

            const shuffled = [...suggestedQuestions].sort(() => 0.5 - Math.random());
            setCurrentSuggestions(shuffled.slice(0, 3));

            if (data.sources?.length) {
              setMessages((prev) => [
                ...prev,
                { type: 'sources', text: data.sources.join(', ') },
              ]);
            }
            return;
          }

          const char = fullText.charAt(i);
          setMessages((prev) => {
            const updated = [...prev];
            updated[botIndex] = {
              ...updated[botIndex],
              text: updated[botIndex].text + char,
            };
            return updated;
          });

          i++;
        }, 10);
      }, 10);

    } catch (err) {
      setBotThinking(false);
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { type: 'bot', text: `Error: ${err.message}` },
      ]);
    }
  };

  const stopTyping = () => {
    if (typingIntervalRef.current) {
      clearInterval(typingIntervalRef.current);
      typingIntervalRef.current = null;
      setIsTyping(false);
    }
  };

  const handleSuggestedClick = (question) => {
    setQuery(question);
    setTimeout(() => {
      document.querySelector('.chat-form button[type="submit"]').click();
    }, 0);
  };

  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages, isTyping, botThinking]);

  return (
    <>
      {!isOpen && (
        <button className="chat-icon" onClick={() => setIsOpen(true)}>
          💬
        </button>
      )}

      {isOpen && (
        <div className="chat-popup">
          <div className="chat-header">
            <h2>PolicyPal</h2>
            <button className="minimize-button" onClick={() => setIsOpen(false)} title="Close Chat">
              ⤬
            </button>
          </div>

          <div className="chatbox" ref={chatboxRef}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.type}`}>
                <strong>{msg.type === 'user' ? 'You' : msg.type === 'bot' ? 'Bot' : 'Sources'}:</strong> {msg.text}
              </div>
            ))}

            {botThinking && (
              <div className="message bot">
                <em>Bot is thinking...</em>
              </div>
            )}

            {!isTyping && !botThinking && currentSuggestions.length > 0 && (
              <div className="suggested-questions">
                <p>Suggested questions:</p>
                <div className="suggestion-buttons">
                  {currentSuggestions.map((q, i) => (
                    <button key={i} onClick={() => handleSuggestedClick(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="chat-form">
            <input
              type="text"
              placeholder="Type your question..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              required
              disabled={isTyping || botThinking}
            />
            <button
              type={isTyping ? 'button' : 'submit'}
              className={`main-button ${isTyping || botThinking ? 'disabled' : ''}`}
              onClick={isTyping ? stopTyping : null}
              disabled={botThinking}
            >
              {isTyping ? 'Stop Generating' : botThinking ? 'Thinking...' : 'Send'}
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default ChatBox;
