/**
 * SmartHome AI - 类型定义文件
 * 包含所有接口、类型别名和常量定义
 */

// ============================================
// 主题配置接口
// ============================================

/**
 * 颜色主题配置 - 蓝色科技感主题
 */
export interface ThemeColors {
  /** 主色调 - 科技蓝 */
  primary: string;
  /** 主色调深色变体 */
  primaryDark: string;
  /** 主色调浅色变体 */
  primaryLight: string;
  /** 次要色调 */
  secondary: string;
  /** 背景色 */
  background: string;
  /** 表面色（卡片背景） */
  surface: string;
  /** 文字主色 */
  textPrimary: string;
  /** 文字次要色 */
  textSecondary: string;
  /** 错误色 */
  error: string;
  /** 成功色 */
  success: string;
  /** 警告色 */
  warning: string;
}

/**
 * 响应式断点配置
 */
export interface Breakpoints {
  /** 超小屏幕 */
  xs: number;
  /** 小屏幕 */
  sm: number;
  /** 中等屏幕 */
  md: number;
  /** 大屏幕 */
  lg: number;
  /** 超大屏幕 */
  xl: number;
}

/**
 * 全局主题配置接口
 */
export interface ThemeConfig {
  /** 颜色配置 */
  colors: ThemeColors;
  /** 响应式断点 */
  breakpoints: Breakpoints;
  /** 字体配置 */
  typography: {
    fontFamily: string;
    headingFontFamily: string;
  };
  /** 间距配置 */
  spacing: {
    unit: number;
    scale: number[];
  };
}

// ============================================
// API 响应格式接口
// ============================================

/**
 * 统一 API 响应状态码
 */
export type ApiStatusCode = 200 | 201 | 400 | 401 | 403 | 404 | 500;

/**
 * 统一 API 响应格式
 * @template T - 数据负载类型
 */
export interface ApiResponse<T> {
  /** 状态码 */
  statusCode: ApiStatusCode;
  /** 响应消息 */
  message: string;
  /** 数据负载 */
  data: T;
  /** 时间戳 */
  timestamp: string;
}

/**
 * API 错误响应
 */
export interface ApiError {
  /** 错误代码 */
  code: string;
  /** 错误消息 */
  message: string;
  /** 详细错误信息（可选） */
  details?: Record<string, string[]>;
}

// ============================================
// 联系表单接口
// ============================================

/**
 * 联系表单数据类型
 */
export interface ContactFormData {
  /** 姓名 */
  name: string;
  /** 邮箱 */
  email: string;
  /** 公司名称（可选） */
  company?: string;
  /** 职位（可选） */
  position?: string;
  /** 消息内容 */
  message: string;
  /** 感兴趣的业务领域 */
  interestArea?: 'investor' | 'partner' | 'customer' | 'other';
}

/**
 * 表单字段验证规则类型
 */
export interface ValidationRule {
  /** 是否必填 */
  required: boolean;
  /** 最小长度 */
  minLength?: number;
  /** 最大长度 */
  maxLength?: number;
  /** 正则表达式模式 */
  pattern?: RegExp;
  /** 自定义验证函数 */
  validate?: (value: string) => boolean;
  /** 错误消息 */
  errorMessage: string;
}

/**
 * 表单验证状态
 */
export interface FormValidationState {
  /** 字段是否有效 */
  isValid: boolean;
  /** 错误消息 */
  error?: string;
  /** 是否已触摸（用户交互过） */
  isTouched: boolean;
}

/**
 * 联系表单提交响应
 */
export interface ContactFormResponse {
  /** 提交是否成功 */
  success: boolean;
  /** 提交 ID */
  submissionId: string;
  /** 确认消息 */
  confirmationMessage: string;
}

// ============================================
// 组件通用 Props 接口
// ============================================

/**
 * 基础组件 Props
 */
export interface BaseComponentProps {
  /** 组件类名 */
  className?: string;
  /** 组件内联样式 */
  style?: React.CSSProperties;
  /** 子组件 */
  children?: React.ReactNode;
  /** 测试 ID */
  'data-testid'?: string;
}

/**
 * 可点击组件 Props
 */
export interface ClickableComponentProps extends BaseComponentProps {
  /** 点击事件处理 */
  onClick?: () => void;
  /** 是否禁用 */
  disabled?: boolean;
  /** 加载状态 */
  isLoading?: boolean;
}

/**
 * 页面组件 Props
 */
export interface PageComponentProps extends BaseComponentProps {
  /** 页面标题 */
  pageTitle: string;
  /** 页面描述 */
  pageDescription?: string;
}

// ============================================
// 产品特性数据类型
// ============================================

/**
 * 产品特性项
 */
export interface FeatureItem {
  /** 特性 ID */
  id: string;
  /** 特性标题 */
  title: string;
  /** 特性描述 */
  description: string;
  /** 特性图标（可以是组件或图片路径） */
  icon: string;
  /** 特性类别 */
  category: 'voice' | 'automation' | 'integration' | 'security';
}

/**
 * 自动化场景类型
 */
export interface AutomationScene {
  /** 场景 ID */
  id: string;
  /** 场景名称 */
  name: string;
  /** 场景描述 */
  description: string;
  /** 触发条件 */
  triggers: string[];
  /** 执行动作 */
  actions: string[];
  /** 场景图标 */
  icon: string;
}

/**
 * 设备类型
 */
export interface DeviceType {
  /** 设备类型 ID */
  id: string;
  /** 设备名称 */
  name: string;
  /** 设备类别 */
  category: 'lighting' | 'climate' | 'security' | 'entertainment' | 'appliance';
  /** 支持的功能 */
  capabilities: string[];
  /** 设备图标 */
  icon: string;
}

// ============================================
// 技术架构数据类型
// ============================================

/**
 * 架构层级节点（用于技术架构图展示）
 */
export interface ArchitectureNode {
  /** 节点 ID */
  id: string;
  /** 节点名称 */
  name: string;
  /** 节点描述 */
  description: string;
  /** 节点类型 */
  type: 'frontend' | 'backend' | 'database' | 'cloud' | 'device' | 'api';
  /** 子节点（用于层级展示） */
  children?: ArchitectureNode[];
  /** 连接关系 */
  connections?: string[];
  /** 是否可交互展示详情 */
  isInteractive?: boolean;
  /** 详情内容（当 isInteractive 为 true 时） */
  details?: {
    technologies: string[];
    responsibilities: string[];
    metrics?: {
      latency?: string;
      throughput?: string;
      availability?: string;
    };
  };
}

/**
 * 技术架构图数据
 */
export interface ArchitectureDiagram {
  /** 图表标题 */
  title: string;
  /** 图表描述 */
  description: string;
  /** 架构节点 */
  nodes: ArchitectureNode[];
  /** 图例说明 */
  legend: {
    type: ArchitectureNode['type'];
    color: string;
    label: string;
  }[];
}

// ============================================
// 导航接口
// ============================================

/**
 * 导航菜单项
 */
export interface NavItem {
  /** 菜单项 ID */
  id: string;
  /** 菜单项标签 */
  label: string;
  /** 菜单项路径 */
  path: string;
  /** 子菜单项 */
  children?: NavItem[];
  /** 是否外部链接 */
  isExternal?: boolean;
  /** 图标 */
  icon?: string;
}

// ============================================
// 常量定义
// ============================================

/**
 * 默认主题配置（蓝色科技感）
 */
export const DEFAULT_THEME: ThemeConfig = {
  colors: {
    primary: '#2563EB',
    primaryDark: '#1D4ED8',
    primaryLight: '#3B82F6',
    secondary: '#06B6D4',
    background: '#0F172A',
    surface: '#1E293B',
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    error: '#EF4444',
    success: '#10B981',
    warning: '#F59E0B',
  },
  breakpoints: {
    xs: 0,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    headingFontFamily: "'Orbitron', 'Inter', sans-serif",
  },
  spacing: {
    unit: 8,
    scale: [0, 4, 8, 12, 16, 24, 32, 48, 64],
  },
};

/**
 * 联系表单验证规则配置
 */
export const CONTACT_FORM_VALIDATION: Record<keyof ContactFormData, ValidationRule> = {
  name: {
    required: true,
    minLength: 2,
    maxLength: 50,
    errorMessage: '姓名必须为 2-50 个字符',
  },
  email: {
    required: true,
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    errorMessage: '请输入有效的邮箱地址',
  },
  company: {
    required: false,
    maxLength: 100,
    errorMessage: '公司名称最多 100 个字符',
  },
  position: {
    required: false,
    maxLength: 50,
    errorMessage: '职位最多 50 个字符',
  },
  message: {
    required: true,
    minLength: 10,
    maxLength: 1000,
    errorMessage: '消息必须为 10-1000 个字符',
  },
  interestArea: {
    required: false,
    errorMessage: '请选择感兴趣的业务领域',
  },
};

/**
 * 导航菜单配置
 */
export const NAVIGATION_ITEMS: NavItem[] = [
  { id: 'home', label: '首页', path: '/' },
  { id: 'features', label: '产品特性', path: '/features' },
  { id: 'architecture', label: '技术架构', path: '/architecture' },
  { id: 'contact', label: '联系我们', path: '/contact' },
];
