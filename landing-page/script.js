document.addEventListener('DOMContentLoaded', () => {
    // Header Scroll Effect
    const header = document.querySelector('.header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // Intersection Observer for Fade-in Animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card, .section-title').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease-out';
        observer.observe(el);
    });

    // Chat Simulation
    const chatContainer = document.querySelector('.chat-ui');
    if (chatContainer) {
        const messages = [
            { role: 'user', text: "I spent $45 on groceries today", delay: 1000 },
            { role: 'ai', text: "✅ Added $45 expense in Food category.", delay: 2000 },
            { role: 'ai', text: "Based on your spending, you're at 35% of your monthly budget. Great job staying on track! 📉", delay: 3500 }
        ];

        let currentIndex = 0;

        function addMessage() {
            if (currentIndex >= messages.length) return;

            const msg = messages[currentIndex];
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-message ${msg.role}`;
            msgDiv.style.animationDelay = '0s'; // Reset for JS insertion
            
            msgDiv.innerHTML = `
                <div class="chat-bubble">
                    ${msg.text}
                </div>
            `;

            chatContainer.appendChild(msgDiv);
            currentIndex++;

            if (currentIndex < messages.length) {
                setTimeout(addMessage, messages[currentIndex].delay - messages[currentIndex-1]?.delay || 1000);
            }
        }

        // Start chat simulation when visible
        const chatObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting && currentIndex === 0) {
                // Clear initial static content if any, or just append
                chatContainer.innerHTML = ''; 
                setTimeout(addMessage, 500);
                chatObserver.disconnect();
            }
        });

        chatObserver.observe(chatContainer);
    }
});
