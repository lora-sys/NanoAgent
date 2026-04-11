import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';

const HomePage: React.FC = () => {
  const [activeFeature, setActiveFeature] = useState<number>(0);

  const features = [
    {
      id: 1,
      title: '智能语音助手',
      description: '支持自然语言处理，理解您的每一个指令，让家居控制更简单',
      icon: '🎤',
      details: ['多语言支持', '离线识别', '个性化语音模型']
    },
    {
      id: 2,
      title: '设备智能联动',
      description: '全屋设备互联互通，一键场景切换，打造真正的智慧生活',
      icon: '🔗',
      details: ['跨品牌兼容', '毫秒级响应', '自动化规则引擎']
    },
    {
      id: 3,
      title: '自动化场景',
      description: '根据时间、位置、环境自动触发预设场景，智能无需等待',
      icon: '⚡',
      details: ['地理围栏触发', '环境感知', '学习用户习惯']
    }
  ];

  const stats = [
    { value: '10M+', label: '连接设备' },
    { value: '99.9%', label: '系统可用性' },
    { value: '50+', label: '合作品牌' },
    { value: '24/7', label: '技术支持' }
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            SmartHome <span className="highlight">AI</span>
          </h1>
          <p className="hero-subtitle">
            重新定义智能家居体验，让科技融入生活的每一刻
          </p>
          <div className="hero-cta">
            <Link to="/contact" className="btn btn-primary">
              联系合作
            </Link>
            <Link to="/features" className="btn btn-secondary">
              了解产品
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="smart-home-demo">
            <div className="device device-light"></div>
            <div className="device device-thermostat"></div>
            <div className="device device-camera"></div>
            <div className="device device-lock"></div>
            <div className="hub-center">
              <span>AI Hub</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats-section">
        <div className="stats-container">
          {stats.map((stat, index) => (
            <div key={index} className="stat-item">
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2 className="section-title">核心功能</h2>
        <div className="features-grid">
          <div className="features-list">
            {features.map((feature, index) => (
              <div
                key={feature.id}
                className={`feature-item ${activeFeature === index ? 'active' : ''}`}
                onClick={() => setActiveFeature(index)}
              >
                <span className="feature-icon">{feature.icon}</span>
                <div className="feature-info">
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="feature-detail">
            <div className="feature-detail-card">
              <h3>{features[activeFeature].title}</h3>
              <ul>
                {features[activeFeature].details.map((detail, idx) => (
                  <li key={idx}>{detail}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>准备好升级您的智能家居体验了吗？</h2>
          <p>与行业领先者合作，共同开创智能生活新纪元</p>
          <Link to="/contact" className="btn btn-primary btn-large">
            立即联系
          </Link>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
