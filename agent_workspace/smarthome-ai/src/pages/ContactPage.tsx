import React, { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';

interface FormData {
  name: string;
  email: string;
  company: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

const ContactPage: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    company: '',
    message: ''
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = '姓名不能为空';
    }
    
    if (!formData.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }
    
    if (!formData.message.trim()) {
      newErrors.message = '留言内容不能为空';
    } else if (formData.message.trim().length < 10) {
      newErrors.message = '留言内容至少需要 10 个字符';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    // 模拟表单提交
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      console.log('表单提交成功:', formData);
      setSubmitSuccess(true);
      setFormData({ name: '', email: '', company: '', message: '' });
    } catch (error) {
      console.error('提交失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  return (
    <div className="contact-page">
      <section className="page-header">
        <div className="container">
          <h1>联系我们</h1>
          <p>期待与您合作，共创智能未来</p>
        </div>
      </section>

      <section className="contact-section">
        <div className="container">
          <div className="contact-grid">
            <div className="contact-info">
              <h2>获取联系</h2>
              <p>无论是投资合作还是技术咨询，我们都期待与您的交流</p>
              
              <div className="contact-item">
                <div className="icon">📍</div>
                <div>
                  <h4>公司地址</h4>
                  <p>北京市海淀区中关村科技园区</p>
                </div>
              </div>
              
              <div className="contact-item">
                <div className="icon">📧</div>
                <div>
                  <h4>电子邮箱</h4>
                  <p>contact@smarthome-ai.com</p>
                </div>
              </div>
              
              <div className="contact-item">
                <div className="icon">📞</div>
                <div>
                  <h4>联系电话</h4>
                  <p>+86 400-888-8888</p>
                </div>
              </div>
            </div>

            <div className="contact-form-wrapper">
              {submitSuccess ? (
                <div className="success-message">
                  <div className="success-icon">✓</div>
                  <h3>提交成功！</h3>
                  <p>感谢您的留言，我们将在 24 小时内与您联系</p>
                  <button 
                    className="btn btn-primary" 
                    onClick={() => setSubmitSuccess(false)}
                  >
                    发送新消息
                  </button>
                </div>
              ) : (
                <form className="contact-form" onSubmit={handleSubmit}>
                  <h2>在线留言</h2>
                  
                  <div className="form-group">
                    <label htmlFor="name">姓名 *</label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      className={errors.name ? 'error' : ''}
                      placeholder="请输入您的姓名"
                    />
                    {errors.name && <span className="error-message">{errors.name}</span>}
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="email">邮箱 *</label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      className={errors.email ? 'error' : ''}
                      placeholder="请输入您的邮箱"
                    />
                    {errors.email && <span className="error-message">{errors.email}</span>}
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="company">公司</label>
                    <input
                      type="text"
                      id="company"
                      name="company"
                      value={formData.company}
                      onChange={handleChange}
                      placeholder="请输入您的公司名称（选填）"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label htmlFor="message">留言内容 *</label>
                    <textarea
                      id="message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      className={errors.message ? 'error' : ''}
                      placeholder="请输入您想咨询的内容..."
                      rows={5}
                    />
                    {errors.message && <span className="error-message">{errors.message}</span>}
                  </div>
                  
                  <button 
                    type="submit" 
                    className="btn btn-primary btn-full"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? '提交中...' : '发送消息'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default ContactPage;
