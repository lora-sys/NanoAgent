import React, { useState } from 'react';
import './Features.css';

// 类型定义
interface FeatureItem {
  id: number;
  title: string;
  description: string;
  icon: string;
  details: string[];
}

interface FeatureCardProps {
  feature: FeatureItem;
  isActive: boolean;
  onClick: () => void;
}

// 产品特性数据
const featuresData: FeatureItem[] = [
  {
    id: 1,
    title: '智能语音助手',
    description: '自然语言交互，解放双手控制全屋设备',
    icon: '🎤',
    details: [
      '支持多语言识别',
      '上下文理解能力',
      '个性化语音定制',
      '离线语音控制'
    ]
  },
  {
    id: 2,
    title: '设备智能联动',
    description: '跨品牌设备无缝连接，打造统一生态',
    icon: '🔗',
    details: [
      '支持 500+ 品牌设备',
      'Zigbee/WiFi/蓝牙多协议',
      '一键场景切换',
      '设备状态实时同步'
    ]
  },
  {
    id: 3,
    title: '自动化场景',
    description: 'AI 学习用户习惯，自动执行智能场景',
    icon: '⚡',
    details: [
      '行为模式学习',
      '时间触发自动化',
      '条件组合场景',
      '远程场景控制'
    ]
  },
  {
    id: 4,
    title: '安全监控系统',
    description: '全方位家庭安全防护，实时预警通知',
    icon: '🛡️',
    details: [
      '智能门锁联动',
      '摄像头 AI 识别',
      '异常行为检测',
      '紧急联系人通知'
    ]
  },
  {
    id: 5,
    title: '能源管理',
    description: '智能用电分析，节能环保更省钱',
    icon: '💡',
    details: [
      '用电数据可视化',
      '智能节电建议',
      '峰谷电价优化',
      '设备能耗排行'
    ]
  },
  {
    id: 6,
    title: '远程控制',
    description: '随时随地掌控家居，手机就是遥控器',
    icon: '📱',
    details: [
      '全球远程访问',
      '多设备同步',
      '家人权限管理',
      '操作日志记录'
    ]
  }
];

// 特性卡片组件
const FeatureCard: React.FC<FeatureCardProps> = ({ feature, isActive, onClick }) => {
  return (
    <div 
      className={`feature-card ${isActive ? 'active' : ''}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      aria-expanded={isActive}
    >
      <div className="feature-icon">{feature.icon}</div>
      <div className="feature-content">
        <h3 className="feature-title">{feature.title}</h3>
        <p className="feature-description">{feature.description}</p>
        {isActive && (
          <ul className="feature-details">
            {feature.details.map((detail, index) => (
              <li key={index}>{detail}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

// 主特性页面组件
const Features: React.FC = () => {
  const [activeFeature, setActiveFeature] = useState<number>(1);

  const handleFeatureClick = (id: number): void => {
    setActiveFeature(id);
  };

  return (
    <div className="features-page">
      <section className="features-hero">
        <div className="container">
          <h1 className="page-title">产品特性</h1>
          <p className="page-subtitle">
            SmartHome AI 为您提供全方位的智能家居解决方案，
            让科技真正服务于生活
          </p>
        </div>
      </section>

      <section className="features-grid-section">
        <div className="container">
          <div className="features-grid">
            {featuresData.map((feature) => (
              <FeatureCard
                key={feature.id}
                feature={feature}
                isActive={activeFeature === feature.id}
                onClick={() => handleFeatureClick(feature.id)}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="features-stats">
        <div className="container">
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-number">500+</span>
              <span className="stat-label">支持设备品牌</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">99.9%</span>
              <span className="stat-label">系统稳定性</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">10M+</span>
              <span className="stat-label">活跃用户</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">24/7</span>
              <span className="stat-label">技术支持</span>
            </div>
          </div>
        </div>
      </section>

      <section className="features-cta">
        <div className="container">
          <h2>准备好体验智能家居的未来了吗？</h2>
          <p>联系我们的团队，获取专属解决方案</p>
          <a href="/contact" className="cta-button">立即咨询</a>
        </div>
      </section>
    </div>
  );
};

export default Features;
