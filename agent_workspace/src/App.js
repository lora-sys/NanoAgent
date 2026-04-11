import React from 'react';
import './App.css';

function App() {
  return (
    <div className="app">
      {/* 头部导航 */}
      <header className="header">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">GreenEnergy</span>
        </div>
        <nav className="nav">
          <a href="#about">关于我们</a>
          <a href="#business">业务模式</a>
          <a href="#market">市场分析</a>
          <a href="#finance">财务预测</a>
          <a href="#contact">联系我们</a>
        </nav>
      </header>

      {/* 英雄区域 */}
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">清洁能源 · 智慧未来</h1>
          <p className="hero-subtitle">为家庭和企业提供专业太阳能安装解决方案</p>
          <div className="hero-stats">
            <div className="stat-item">
              <span className="stat-number">500+</span>
              <span className="stat-label">已安装项目</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">98%</span>
              <span className="stat-label">客户满意度</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">30%</span>
              <span className="stat-label">平均节能率</span>
            </div>
          </div>
          <button className="cta-button">获取商业计划书</button>
        </div>
        <div className="hero-visual">
          <div className="solar-panel-animation">
            <div className="panel"></div>
            <div className="panel"></div>
            <div className="panel"></div>
          </div>
        </div>
      </section>

      {/* 业务模式 */}
      <section id="business" className="section business-model">
        <h2 className="section-title">业务模式</h2>
        <div className="cards-container">
          <div className="card">
            <div className="card-icon">🏠</div>
            <h3>住宅安装</h3>
            <p>为家庭用户提供定制化太阳能系统安装服务</p>
          </div>
          <div className="card">
            <div className="card-icon">🏢</div>
            <h3>商业安装</h3>
            <p>为企业客户提供大规模太阳能解决方案</p>
          </div>
          <div className="card">
            <div className="card-icon">🔧</div>
            <h3>运维服务</h3>
            <p>提供系统维护、监控和优化服务</p>
          </div>
        </div>
      </section>

      {/* 市场分析 */}
      <section id="market" className="section market-analysis">
        <h2 className="section-title">市场分析</h2>
        <div className="market-content">
          <div className="market-stat">
            <h3>$500 亿</h3>
            <p>2025 年全球太阳能市场规模</p>
          </div>
          <div className="market-stat">
            <h3>25%</h3>
            <p>年复合增长率</p>
          </div>
          <div className="market-stat">
            <h3>政策利好</h3>
            <p>多国碳中和目标推动</p>
          </div>
        </div>
      </section>

      {/* 财务预测 */}
      <section id="finance" className="section finance">
        <h2 className="section-title">财务预测</h2>
        <div className="finance-chart">
          <div className="chart-bar" style={{height: '40%'}}>
            <span>第一年</span>
            <span>$2M</span>
          </div>
          <div className="chart-bar" style={{height: '60%'}}>
            <span>第二年</span>
            <span>$5M</span>
          </div>
          <div className="chart-bar" style={{height: '85%'}}>
            <span>第三年</span>
            <span>$12M</span>
          </div>
          <div className="chart-bar" style={{height: '100%'}}>
            <span>第四年</span>
            <span>$25M</span>
          </div>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="footer">
        <p>&copy; 2024 GreenEnergy. 为可持续未来而努力</p>
        <div className="contact-info">
          <span>📧 contact@greenenergy.com</span>
          <span>📞 +1 (555) 123-4567</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
