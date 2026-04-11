import React, { useState } from 'react';
import { Feature, FeatureCategory } from '../types';

interface FeatureCardProps {
  feature: Feature;
  index: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ feature, index }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="feature-card"
      style={{ animationDelay: `${index * 0.1}s` }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="feature-icon" style={{ backgroundColor: feature.color }}>
        {feature.icon}
      </div>
      <h3 className="feature-title">{feature.title}</h3>
      <p className="feature-description">{feature.description}</p>
      <ul className="feature-list">
        {feature.details.map((detail, idx) => (
          <li key={idx} className="feature-list-item">
            <span className="checkmark">✓</span> {detail}
          </li>
        ))}
      </ul>
      <div className={`feature-learn-more ${isHovered ? 'visible' : ''}`}>
        了解更多 →
      </div>
    </div>
  );
};

interface CategorySectionProps {
  category: FeatureCategory;
  features: Feature[];
}

const CategorySection: React.FC<CategorySectionProps> = ({ category, features }) => {
  return (
    <section className="category-section">
      <div className="category-header">
        <h2 className="category-title">{category.title}</h2>
        <p className="category-description">{category.description}</p>
      </div>
      <div className="features-grid">
        {features.map((feature, index) => (
          <FeatureCard key={feature.id} feature={feature} index={index} />
        ))}
      </div>
    </section>
  );
};

const FeaturesPage: React.FC = () => {
  const categories: FeatureCategory[] = [
    {
      id: 'voice-assistant',
      title: '智能语音助手',
      description: '通过自然语言交互，轻松控制家中所有智能设备',
    },
    {
      id: 'device-linkage',
      title: '设备联动',
      description: '跨品牌、跨协议的设备无缝连接与协同工作',
    },
    {
      id: 'automation',
      title: '自动化场景',
      description: '基于时间、位置、状态的智能场景自动触发',
    },
  ];

  const features: Feature[] = [
    {
      id: 'voice-1',
      title: '多语言支持',
      description: '支持中文、英文、日文等 20+ 种语言的语音识别',
      icon: '🎤',
      color: '#3B82F6',
      categoryId: 'voice-assistant',
      details: [
        '98% 语音识别准确率',
        '离线语音控制支持',
        '方言识别优化',
        '声纹识别安全验证',
      ],
    },
    {
      id: 'voice-2',
      title: '自然对话理解',
      description: '理解上下文的多轮对话，支持复杂指令解析',
      icon: '💬',
      color: '#8B5CF6',
      categoryId: 'voice-assistant',
      details: [
        '上下文记忆能力',
        '模糊指令智能补全',
        '多意图同时处理',
        '个性化语音模型',
      ],
    },
    {
      id: 'linkage-1',
      title: '跨协议兼容',
      description: '支持 Zigbee、Z-Wave、WiFi、Bluetooth 等多种协议',
      icon: '🔗',
      color: '#10B981',
      categoryId: 'device-linkage',
      details: [
        '500+ 品牌设备兼容',
        '自动协议识别',
        ' Mesh 网络优化',
        '低延迟设备响应',
      ],
    },
    {
      id: 'linkage-2',
      title: '场景联动引擎',
      description: '一键创建复杂的设备联动规则',
      icon: '⚡',
      color: '#F59E0B',
      categoryId: 'device-linkage',
      details: [
        '可视化规则编辑器',
        '条件触发器库',
        '延迟执行支持',
        '联动日志追踪',
      ],
    },
    {
      id: 'auto-1',
      title: '智能场景模板',
      description: '预设常用场景，一键启用个性化智能家居体验',
      icon: '🏠',
      color: '#EC4899',
      categoryId: 'automation',
      details: [
        '回家/离家模式',
        '睡眠/起床场景',
        '观影模式',
        '安防布防场景',
      ],
    },
    {
      id: 'auto-2',
      title: 'AI 学习优化',
      description: '基于用户习惯的自适应场景推荐与优化',
      icon: '🧠',
      color: '#6366F1',
      categoryId: 'automation',
      details: [
        '行为模式学习',
        '能耗优化建议',
        '异常行为预警',
        '场景效果评估',
      ],
    },
  ];

  return (
    <div className="features-page">
      <header className="features-header">
        <h1 className="page-title">产品特性</h1>
        <p className="page-subtitle">
          SmartHome AI 为您提供全方位的智能家居解决方案
        </p>
      </header>

      <div className="features-content">
        {categories.map((category) => {
          const categoryFeatures = features.filter(
            (f) => f.categoryId === category.id
          );
          return (
            <CategorySection
              key={category.id}
              category={category}
              features={categoryFeatures}
            />
          );
        })}
      </div>

      <section className="features-cta">
        <div className="cta-content">
          <h2>准备好升级您的智能家居体验了吗？</h2>
          <p>联系我们，获取专属解决方案演示</p>
          <a href="/contact" className="cta-button">
            立即咨询
          </a>
        </div>
      </section>
    </div>
  );
};

export default FeaturesPage;
