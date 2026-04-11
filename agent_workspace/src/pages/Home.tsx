import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// 类型定义
interface FeatureCard {
  id: number;
  title: string;
  description: string;
  icon: string;
}

interface StatItem {
  value: string;
  label: string;
}

// 组件样式接口
interface SectionProps {
  children: React.ReactNode;
  className?: string;
}

// 核心功能数据
const coreFeatures: FeatureCard[] = [
  {
    id: 1,
    title: '智能语音助手',
    description: '支持自然语言交互，精准识别用户指令，实现全屋智能设备语音控制',
    icon: '🎤'
  },
  {
    id: 2,
    title: '设备联动',
    description: '跨品牌设备无缝连接，打造统一智能家居生态，实现设备间智能协作',
    icon: '🔗'
  },
  {
    id: 3,
    title: '自动化场景',
    description: '自定义智能场景，根据时间、位置、环境自动触发，让生活更便捷',
    icon: '⚡'
  },
  {
    id: 4,
    title: '安全监控',
    description: '24 小时实时监控，智能异常检测，多重安全保障守护家庭安全',
    icon: '🛡️'
  }
];

// 统计数据
const stats: StatItem[] = [
  { value: '10M+', label: '连接设备' },
  { value: '99.9%', label: '系统稳定性' },
  { value: '500+', label: '合作品牌' },
  { value: '24/7', label: '技术支持' }
];

// 分段组件
const Section: React.FC<SectionProps> = ({ children, className = '' }) => (
  <section className={`section ${className}`}>{children}</section>
);

// 功能卡片组件
const FeatureCard: React.FC<FeatureCard> = ({ title, description, icon }) => (
  <div className="feature-card">
    <div className="feature-icon">{icon}</div>
    <h3 className="feature-title">{title}</h3>
    <p className="feature-description">{description}</p>
  </div>
);

// 统计项组件
const StatItem: React.FC<StatItem> = ({ value, label }) => (
  <div className="stat-item">
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
  </div>
);

// 主页面组件
const Home: React.FC = () => {
  const [isVisible, setIsVisible] = useState<boolean>(false);
  const [scrolled, setScrolled] = useState<boolean>(false);

  // 页面加载动画
  useEffect(() => {
    setIsVisible(true);
    
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="home-page">
      {/* 英雄区域 */}
      <Section className="hero-section">
        <div className={`hero-content ${isVisible ? 'visible' : ''}`}>
          <div className="hero-badge">
            <span>🚀 智能家居新纪元</span>
          </div>
          <h1 className="hero-title">
            SmartHome <span className="highlight">AI</span>
          </h1>
          <p className="hero-subtitle">
            重新定义智能生活，让家更懂你
          </p>
          <p className="hero-description">
            基于先进 AI 技术的智能家居控制系统，集成语音助手、设备联动、
            自动化场景于一体，为投资人和合作伙伴打造未来家居解决方案。
          </p>
          <div className="hero-actions">
            <Link to="/features" className="btn btn-primary">
              探索产品特性
            </Link>
            <Link to="/contact" className="btn btn-secondary">
              联系我们
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="floating-elements">
            <div className="float-element float-1">🏠</div>
            <div className="float-element float-2">💡</div>
            <div className="float-element float-3">🔒</div>
            <div className="float-element float-4">📱</div>
          </div>
        </div>
      </Section>

      {/* 核心功能展示 */}
      <Section className="features-section">
        <div className="section-header">
          <h2 className="section-title">核心功能</h2>
          <p className="section-subtitle">
            四大核心模块，构建完整智能家居生态
          </p>
        </div>
        <div className="features-grid">
          {coreFeatures.map((feature) => (
            <FeatureCard key={feature.id} {...feature} />
          ))}
        </div>
      </Section>

      {/* 统计数据 */}
      <Section className="stats-section">
        <div className="stats-container">
          {stats.map((stat, index) => (
            <StatItem key={index} {...stat} />
          ))}
        </div>
      </Section>

      {/* 技术优势 */}
      <Section className="advantage-section">
        <div className="advantage-content">
          <div className="advantage-text">
            <h2 className="section-title">技术领先优势</h2>
            <ul className="advantage-list">
              <li>
                <span className="check-icon">✓</span>
                基于深度学习的语音识别，准确率高达 98%
              </li>
              <li>
                <span className="check-icon">✓</span>
                支持 500+ 品牌设备，兼容性行业领先
              </li>
              <li>
                <span className="check-icon">✓</span>
                边缘计算架构，响应时间<100ms
              </li>
              <li>
                <span className="check-icon">✓</span>
                端到端加密，保障用户隐私安全
              </li>
              <li>
                <span className="check-icon">✓</span>
                云端 + 本地双模式，断网仍可运行
              </li>
            </ul>
            <Link to="/architecture" className="btn btn-outline">
              查看技术架构
            </Link>
          </div>
          <div className="advantage-visual">
            <div className="tech-diagram">
              <div className="diagram-layer layer-1">AI 引擎</div>
              <div className="diagram-layer layer-2">控制中枢</div>
              <div className="diagram-layer layer-3">设备网络</div>
            </div>
          </div>
        </div>
      </Section>

      {/* CTA 区域 */}
      <Section className="cta-section">
        <div className="cta-content">
          <h2 className="cta-title">准备好开启智能生活了吗？</h2>
          <p className="cta-description">
            与我们合作，共同构建未来智能家居生态
          </p>
          <div className="cta-actions">
            <Link to="/contact" className="btn btn-primary btn-large">
              成为合作伙伴
            </Link>
            <Link to="/features" className="btn btn-outline btn-large">
              了解更多
            </Link>
          </div>
        </div>
      </Section>

      {/* 页脚 */}
      <footer className="home-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>SmartHome AI</h3>
            <p>让家更懂你</p>
          </div>
          <div className="footer-links">
            <Link to="/">首页</Link>
            <Link to="/features">产品特性</Link>
            <Link to="/architecture">技术架构</Link>
            <Link to="/contact">联系我们</Link>
          </div>
          <div className="footer-copy">
            © 2024 SmartHome AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
