import React from 'react';
import './LandingPage.css';

interface LandingPageProps {
  onGetStarted: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  return (
    <div className="landing">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            Your AI Financial Advisor
            <span className="gradient-text"> That Actually Gets You</span>
          </h1>
          <p className="hero-subtitle">
            Chat naturally about your finances. Get intelligent insights, automated tracking, 
            and personalized advice—all powered by AI.
          </p>
          <div className="hero-cta">
            <button className="btn-primary" onClick={onGetStarted}>
              Start Free Today
            </button>
            <button className="btn-secondary" onClick={() => {
              document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
            }}>
              See How It Works
            </button>
          </div>
          <p className="hero-note">No credit card required • 2 minute setup</p>
        </div>
      </section>

      {/* Social Proof */}
      <section className="social-proof">
        <div className="stats">
          <div className="stat">
            <div className="stat-value">$2.4M+</div>
            <div className="stat-label">Money Managed</div>
          </div>
          <div className="stat">
            <div className="stat-value">15K+</div>
            <div className="stat-label">Active Users</div>
          </div>
          <div className="stat">
            <div className="stat-value">4.9/5</div>
            <div className="stat-label">User Rating</div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features">
        <h2 className="section-title">Everything You Need to Master Your Money</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <i className="fas fa-comments"></i>
            </div>
            <h3>Natural Conversations</h3>
            <p>Just chat: "I spent $45 on groceries" and your AI handles the rest—no forms, no hassle.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <i className="fas fa-bullseye"></i>
            </div>
            <h3>Smart Goal Tracking</h3>
            <p>Set goals and get adaptive milestones that adjust to your actual savings rate.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <i className="fas fa-chart-line"></i>
            </div>
            <h3>Real-Time Insights</h3>
            <p>See your financial health score, net worth, and spending patterns at a glance.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <i className="fas fa-bell"></i>
            </div>
            <h3>Smart Notifications</h3>
            <p>Budget alerts, bill reminders, and milestone celebrations—never miss what matters.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <i className="fas fa-wallet"></i>
            </div>
            <h3>Dynamic Budgeting</h3>
            <p>AI-powered budget adjustments based on your behavior and priorities.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <i className="fas fa-chart-area"></i>
            </div>
            <h3>Cash Flow Forecasting</h3>
            <p>90-day projections to identify potential shortfalls before they happen.</p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="how-it-works">
        <h2 className="section-title">Get Started in 3 Simple Steps</h2>
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Create Your Account</h3>
            <p>Sign up in 2 minutes. No credit card, no commitment.</p>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <h3>Chat With Your AI</h3>
            <p>Tell it about your income, expenses, and goals in plain English.</p>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <h3>Watch the Magic</h3>
            <p>Get insights, alerts, and recommendations tailored to you.</p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials">
        <h2 className="section-title">Loved by Thousands</h2>
        <div className="testimonials-grid">
          <div className="testimonial">
            <div className="testimonial-stars">★★★★★</div>
            <p>"Finally, a financial app that doesn't feel like homework. I just chat and it handles everything."</p>
            <div className="testimonial-author">— Sarah M., Designer</div>
          </div>
          <div className="testimonial">
            <div className="testimonial-stars">★★★★★</div>
            <p>"The AI caught a subscription I forgot about. Saved me $180/year without lifting a finger."</p>
            <div className="testimonial-author">— James K., Developer</div>
          </div>
          <div className="testimonial">
            <div className="testimonial-stars">★★★★★</div>
            <p>"I've tried 5 budgeting apps. This is the only one I actually use daily. Game changer."</p>
            <div className="testimonial-author">— Maria L., Teacher</div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <h2>Ready to Take Control?</h2>
        <p>Join thousands who've transformed their financial lives with AI.</p>
        <button className="btn-primary btn-large" onClick={onGetStarted}>
          Start Your Free Account
        </button>
        <p className="cta-note">Free forever • No credit card • 2 minute setup</p>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>FinWise</h3>
            <p>AI-powered financial planning for everyone</p>
          </div>
          <div className="footer-links">
            <div className="footer-column">
              <h4>Product</h4>
              <a href="#features">Features</a>
              <a href="#how-it-works">How It Works</a>
              <a href="#pricing">Pricing</a>
            </div>
            <div className="footer-column">
              <h4>Company</h4>
              <a href="#about">About</a>
              <a href="#privacy">Privacy</a>
              <a href="#terms">Terms</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2025 FinWise. Built for better financial futures.</p>
        </div>
      </footer>
    </div>
  );
};
