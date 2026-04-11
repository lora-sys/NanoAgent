import React, { useState, FormEvent, ChangeEvent } from 'react';
import '../styles/Contact.css';

// TypeScript 接口定义
interface FormData {
  name: string;
  email: string;
  phone: string;
  company: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
}

interface FormState {
  data: FormData;
  errors: FormErrors;
  isSubmitting: boolean;
  submitSuccess: boolean;
  submitError: string | null;
}

const Contact: React.FC = () => {
  // 表单状态管理
  const [formState, setFormState] = useState<FormState>({
    data: {
      name: '',
      email: '',
      phone: '',
      company: '',
      message: '',
    },
    errors: {},
    isSubmitting: false,
    submitSuccess: false,
    submitError: null,
  });

  // 验证规则
  const validateField = (name: string, value: string): string | undefined => {
    switch (name) {
      case 'name':
        if (!value.trim()) return '姓名不能为空';
        if (value.trim().length < 2) return '姓名至少需要 2 个字符';
        return undefined;
      
      case 'email':
        if (!value.trim()) return '邮箱不能为空';
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) return '请输入有效的邮箱地址';
        return undefined;
      
      case 'phone':
        if (!value.trim()) return undefined; // 可选字段
        const phoneRegex = /^1[3-9]\d{9}$/;
        if (!phoneRegex.test(value)) return '请输入有效的 11 位手机号';
        return undefined;
      
      case 'message':
        if (!value.trim()) return '留言内容不能为空';
        if (value.trim().length < 10) return '留言内容至少需要 10 个字符';
        return undefined;
      
      default:
        return undefined;
    }
  };

  // 验证整个表单
  const validateForm = (): boolean => {
    const { data } = formState;
    const errors: FormErrors = {};

    const nameError = validateField('name', data.name);
    if (nameError) errors.name = nameError;

    const emailError = validateField('email', data.email);
    if (emailError) errors.email = emailError;

    const phoneError = validateField('phone', data.phone);
    if (phoneError) errors.phone = phoneError;

    const messageError = validateField('message', data.message);
    if (messageError) errors.message = messageError;

    setFormState(prev => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  // 处理输入变化
  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    setFormState(prev => ({
      ...prev,
      data: {
        ...prev.data,
        [name]: value,
      },
      // 实时清除该字段的错误
      errors: {
        ...prev.errors,
        [name]: undefined,
      },
    }));
  };

  // 处理表单提交
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    // 验证表单
    if (!validateForm()) {
      return;
    }

    // 设置提交中状态
    setFormState(prev => ({
      ...prev,
      isSubmitting: true,
      submitError: null,
    }));

    try {
      // 模拟 API 调用（实际项目中替换为真实接口）
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // 模拟成功响应
      console.log('表单提交数据:', formState.data);
      
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        submitSuccess: true,
        data: {
          name: '',
          email: '',
          phone: '',
          company: '',
          message: '',
        },
      }));

      // 3 秒后重置成功状态
      setTimeout(() => {
        setFormState(prev => ({ ...prev, submitSuccess: false }));
      }, 3000);
      
    } catch (error) {
      setFormState(prev => ({
        ...prev,
        isSubmitting: false,
        submitError: '提交失败，请稍后重试',
      }));
    }
  };

  return (
    <div className="contact-page">
      <div className="contact-container">
        {/* 页面标题 */}
        <div className="contact-header">
          <h1 className="contact-title">联系我们</h1>
          <p className="contact-subtitle">
            期待与您合作，共同打造智能未来
          </p>
        </div>

        {/* 联系信息卡片 */}
        <div className="contact-info-grid">
          <div className="info-card">
            <div className="info-icon">📍</div>
            <h3>公司地址</h3>
            <p>北京市海淀区中关村科技园</p>
            <p>智能大厦 A 座 18 层</p>
          </div>
          <div className="info-card">
            <div className="info-icon">📧</div>
            <h3>电子邮箱</h3>
            <p>business@smarthome-ai.com</p>
            <p>support@smarthome-ai.com</p>
          </div>
          <div className="info-card">
            <div className="info-icon">📞</div>
            <h3>联系电话</h3>
            <p>400-888-6688</p>
            <p>+86 10 8888 6666</p>
          </div>
        </div>

        {/* 联系表单 */}
        <div className="contact-form-section">
          <h2 className="form-title">商务合作咨询</h2>
          
          {formState.submitSuccess && (
            <div className="success-message">
              <span className="success-icon">✓</span>
              <p>提交成功！我们将尽快与您联系</p>
            </div>
          )}

          {formState.submitError && (
            <div className="error-message">
              <span className="error-icon">!</span>
              <p>{formState.submitError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="contact-form" noValidate>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name" className="form-label">
                  姓名 <span className="required">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formState.data.name}
                  onChange={handleInputChange}
                  className={`form-input ${formState.errors.name ? 'error' : ''}`}
                  placeholder="请输入您的姓名"
                  disabled={formState.isSubmitting}
                  aria-invalid={!!formState.errors.name}
                  aria-describedby={formState.errors.name ? 'name-error' : undefined}
                />
                {formState.errors.name && (
                  <span id="name-error" className="error-text">
                    {formState.errors.name}
                  </span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  邮箱 <span className="required">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formState.data.email}
                  onChange={handleInputChange}
                  className={`form-input ${formState.errors.email ? 'error' : ''}`}
                  placeholder="请输入您的邮箱"
                  disabled={formState.isSubmitting}
                  aria-invalid={!!formState.errors.email}
                  aria-describedby={formState.errors.email ? 'email-error' : undefined}
                />
                {formState.errors.email && (
                  <span id="email-error" className="error-text">
                    {formState.errors.email}
                  </span>
                )}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="phone" className="form-label">
                  手机号 <span className="optional">（选填）</span>
                </label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formState.data.phone}
                  onChange={handleInputChange}
                  className={`form-input ${formState.errors.phone ? 'error' : ''}`}
                  placeholder="请输入您的手机号"
                  disabled={formState.isSubmitting}
                  aria-invalid={!!formState.errors.phone}
                  aria-describedby={formState.errors.phone ? 'phone-error' : undefined}
                />
                {formState.errors.phone && (
                  <span id="phone-error" className="error-text">
                    {formState.errors.phone}
                  </span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="company" className="form-label">
                  公司名称 <span className="optional">（选填）</span>
                </label>
                <input
                  type="text"
                  id="company"
                  name="company"
                  value={formState.data.company}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="请输入您的公司名称"
                  disabled={formState.isSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="message" className="form-label">
                留言内容 <span className="required">*</span>
              </label>
              <textarea
                id="message"
                name="message"
                value={formState.data.message}
                onChange={handleInputChange}
                className={`form-textarea ${formState.errors.message ? 'error' : ''}`}
                placeholder="请描述您的合作意向或需求..."
                rows={5}
                disabled={formState.isSubmitting}
                aria-invalid={!!formState.errors.message}
                aria-describedby={formState.errors.message ? 'message-error' : undefined}
              />
              {formState.errors.message && (
                <span id="message-error" className="error-text">
                  {formState.errors.message}
                </span>
              )}
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="submit-button"
                disabled={formState.isSubmitting}
              >
                {formState.isSubmitting ? (
                  <>
                    <span className="loading-spinner"></span>
                    提交中...
                  </>
                ) : (
                  '提交咨询'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Contact;
