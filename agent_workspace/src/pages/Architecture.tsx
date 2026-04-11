import React, { useState } from 'react';
import './Architecture.css';

interface ArchitectureNode {
  id: string;
  label: string;
  description: string;
  color: string;
  connections: string[];
}

interface ArchitectureLayer {
  name: string;
  nodes: ArchitectureNode[];
}

const Architecture: React.FC = () => {
  const [selectedNode, setSelectedNode] = useState<ArchitectureNode | null>(null);

  const layers: ArchitectureLayer[] = [
    {
      name: '用户交互层',
      nodes: [
        {
          id: 'voice',
          label: '语音助手',
          description: '支持自然语言处理，实现语音控制智能家居设备',
          color: '#3B82F6',
          connections: ['cloud', 'automation']
        },
        {
          id: 'app',
          label: '移动应用',
          description: 'iOS/Android 跨平台应用，远程控制家中设备',
          color: '#3B82F6',
          connections: ['cloud']
        },
        {
          id: 'web',
          label: 'Web 控制台',
          description: '浏览器端管理界面，支持多设备同步',
          color: '#3B82F6',
          connections: ['cloud']
        }
      ]
    },
    {
      name: '云端服务层',
      nodes: [
        {
          id: 'cloud',
          label: 'SmartHome Cloud',
          description: '核心云服务，处理设备数据同步和用户认证',
          color: '#8B5CF6',
          connections: ['database', 'ai', 'automation']
        },
        {
          id: 'ai',
          label: 'AI 引擎',
          description: '机器学习模型，优化自动化场景和能耗管理',
          color: '#8B5CF6',
          connections: ['database']
        },
        {
          id: 'automation',
          label: '自动化引擎',
          description: '规则引擎，执行预设场景和智能联动',
          color: '#8B5CF6',
          connections: ['devices']
        }
      ]
    },
    {
      name: '数据存储层',
      nodes: [
        {
          id: 'database',
          label: '时序数据库',
          description: '存储设备历史数据和用户行为记录',
          color: '#10B981',
          connections: []
        }
      ]
    },
    {
      name: '设备连接层',
      nodes: [
        {
          id: 'devices',
          label: '智能设备网关',
          description: '支持 Zigbee、Z-Wave、WiFi、Bluetooth 多协议',
          color: '#F59E0B',
          connections: []
        },
        {
          id: 'sensors',
          label: '传感器网络',
          description: '温湿度、光照、运动、烟雾等传感器',
          color: '#F59E0B',
          connections: ['devices']
        },
        {
          id: 'actuators',
          label: '执行器网络',
          description: '灯光、窗帘、空调、门锁等控制设备',
          color: '#F59E0B',
          connections: ['devices']
        }
      ]
    }
  ];

  const handleNodeClick = (node: ArchitectureNode) => {
    setSelectedNode(node);
  };

  return (
    <div className="architecture-page">
      <div className="architecture-header">
        <h1>技术架构</h1>
        <p className="subtitle">SmartHome AI 系统架构设计</p>
      </div>

      <div className="architecture-content">
        <div className="architecture-diagram">
          {layers.map((layer, layerIndex) => (
            <div key={layer.name} className="architecture-layer">
              <h3 className="layer-title">{layer.name}</h3>
              <div className="layer-nodes">
                {layer.nodes.map((node) => (
                  <div
                    key={node.id}
                    className={`architecture-node ${selectedNode?.id === node.id ? 'selected' : ''}`}
                    style={{ borderColor: node.color }}
                    onClick={() => handleNodeClick(node)}
                  >
                    <div
                      className="node-icon"
                      style={{ backgroundColor: node.color }}
                    >
                      <span>{node.label.charAt(0)}</span>
                    </div>
                    <span className="node-label">{node.label}</span>
                  </div>
                ))}
              </div>
              {layerIndex < layers.length - 1 && (
                <div className="layer-connector">
                  <div className="connector-line"></div>
                  <span>↓</span>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="architecture-details">
          <h2>组件详情</h2>
          {selectedNode ? (
            <div className="node-detail-card">
              <div
                className="detail-header"
                style={{ backgroundColor: selectedNode.color }}
              >
                <h3>{selectedNode.label}</h3>
                <span className="node-id">{selectedNode.id}</span>
              </div>
              <div className="detail-body">
                <p>{selectedNode.description}</p>
                {selectedNode.connections.length > 0 && (
                  <div className="connections">
                    <h4>连接组件:</h4>
                    <ul>
                      {selectedNode.connections.map((conn) => (
                        <li key={conn}>{conn}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="node-detail-card empty">
              <p>点击架构图中的组件查看详情</p>
            </div>
          )}

          <div className="tech-stack">
            <h2>技术栈</h2>
            <div className="tech-grid">
              <div className="tech-item">
                <span className="tech-icon">⚛️</span>
                <span>React 18</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">📘</span>
                <span>TypeScript 5</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">☁️</span>
                <span>AWS Cloud</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">🔒</span>
                <span>OAuth 2.0</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">📊</span>
                <span>InfluxDB</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">🤖</span>
                <span>TensorFlow</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">📡</span>
                <span>MQTT</span>
              </div>
              <div className="tech-item">
                <span className="tech-icon">🔧</span>
                <span>Docker</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="architecture-features">
        <h2>架构优势</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">🚀</div>
            <h3>高可用性</h3>
            <p>99.9% SLA 保证，多区域冗余部署</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🔐</div>
            <h3>端到端加密</h3>
            <p>TLS 1.3 + AES-256 双重加密保护</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>低延迟</h3>
            <p>边缘计算节点，响应时间<50ms</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">📈</div>
            <h3>可扩展</h3>
            <p>支持百万级设备并发连接</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Architecture;
