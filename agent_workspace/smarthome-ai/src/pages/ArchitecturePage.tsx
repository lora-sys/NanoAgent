import React, { useState } from 'react';
import { ArchitectureDiagram } from '../components/ArchitectureDiagram';

interface TechStackItem {
  name: string;
  description: string;
  icon: string;
}

interface ArchitectureLayer {
  title: string;
  components: string[];
  color: string;
}

const ArchitecturePage: React.FC = () => {
  const [activeLayer, setActiveLayer] = useState<number | null>(null);

  const techStack: TechStackItem[] = [
    { name: 'React 18', description: '前端框架，支持并发渲染', icon: '⚛️' },
    { name: 'TypeScript', description: '类型安全的 JavaScript 超集', icon: '📘' },
    { name: 'Node.js', description: '后端运行时环境', icon: '🟢' },
    { name: 'WebSocket', description: '实时双向通信协议', icon: '🔌' },
    { name: 'MQTT', description: '物联网消息协议', icon: '📡' },
    { name: 'Redis', description: '缓存与消息队列', icon: '🔴' },
  ];

  const layers: ArchitectureLayer[] = [
    {
      title: '用户交互层',
      components: ['Web 应用', '移动 App', '语音助手', '智能面板'],
      color: '#3B82F6',
    },
    {
      title: '应用服务层',
      components: ['API 网关', '身份认证', '场景引擎', '设备管理'],
      color: '#10B981',
    },
    {
      title: '核心处理层',
      components: ['AI 引擎', '规则引擎', '数据分析', '消息队列'],
      color: '#8B5CF6',
    },
    {
      title: '设备接入层',
      components: ['MQTT Broker', '协议适配', '设备影子', '边缘计算'],
      color: '#F59E0B',
    },
    {
      title: '物理设备层',
      components: ['智能灯光', '温控系统', '安防设备', '家电控制'],
      color: '#EF4444',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 py-16 px-4">
      <div className="max-w-7xl mx-auto">
        {/* 页面标题 */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-white mb-4">
            技术<span className="text-blue-400">架构</span>
          </h1>
          <p className="text-xl text-blue-200 max-w-3xl mx-auto">
            SmartHome AI 采用分层微服务架构，确保系统的高可用性、可扩展性和安全性
          </p>
        </div>

        {/* 架构图展示 */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 mb-16 border border-blue-500/30">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">系统架构总览</h2>
          <ArchitectureDiagram />
          
          {/* 分层详情 */}
          <div className="mt-12 space-y-4">
            {layers.map((layer, index) => (
              <div
                key={index}
                className="bg-slate-700/50 rounded-xl p-6 cursor-pointer transition-all duration-300 hover:scale-[1.02] border-l-4"
                style={{ borderLeftColor: layer.color }}
                onMouseEnter={() => setActiveLayer(index)}
                onMouseLeave={() => setActiveLayer(null)}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-2xl font-semibold text-white">{layer.title}</h3>
                  <span
                    className="text-sm px-3 py-1 rounded-full text-white"
                    style={{ backgroundColor: layer.color }}
                  >
                    Layer {index + 1}
                  </span>
                </div>
                <div className="flex flex-wrap gap-3">
                  {layer.components.map((component, compIndex) => (
                    <span
                      key={compIndex}
                      className="px-4 py-2 bg-slate-600/50 rounded-lg text-blue-200 text-sm hover:bg-slate-600 transition-colors"
                    >
                      {component}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 技术栈 */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 mb-16 border border-blue-500/30">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">核心技术栈</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {techStack.map((tech, index) => (
              <div
                key={index}
                className="bg-gradient-to-br from-slate-700/50 to-slate-800/50 rounded-xl p-6 hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-300 border border-slate-600/50 hover:border-blue-500/50"
              >
                <div className="text-4xl mb-4">{tech.icon}</div>
                <h3 className="text-xl font-semibold text-white mb-2">{tech.name}</h3>
                <p className="text-blue-200 text-sm">{tech.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* 架构优势 */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-blue-500/30">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">架构优势</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { title: '高可用性', desc: '99.99% SLA 保障，多区域容灾部署', icon: '🛡️' },
              { title: '弹性扩展', desc: '支持百万级设备并发接入', icon: '📈' },
              { title: '低延迟', desc: '边缘计算减少响应时间至 50ms', icon: '⚡' },
              { title: '安全可靠', desc: '端到端加密，符合 GDPR 标准', icon: '🔒' },
            ].map((advantage, index) => (
              <div
                key={index}
                className="text-center p-6 bg-slate-700/30 rounded-xl hover:bg-slate-700/50 transition-colors"
              >
                <div className="text-4xl mb-4">{advantage.icon}</div>
                <h3 className="text-lg font-semibold text-white mb-2">{advantage.title}</h3>
                <p className="text-blue-200 text-sm">{advantage.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitecturePage;
