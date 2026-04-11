/**
 * SmartHome AI - TypeScript 类型定义文件
 * 包含所有接口、类型别名和配置定义
 */

// ============ 主题配置接口 ============

/**
 * 全局主题颜色配置 - 蓝色科技感主题
 */
export interface ThemeColors {
  /** 主色调 - 科技蓝 */
  primary: string;
  /** 主色调浅色变体 */
  primaryLight: string;
  /** 主色调深色变体 */
  primaryDark: string;
  /** 次要色调 */
  secondary: string;
  /** 背景色 */
  background: string;
  /** 表面色（卡片、面板等）*/
  surface: string;
  /** 文字主色 */
  textPrimary: string;
  /** 文字次要色 */
  textSecondary: string;
  /** 成功状态色 */
  success: string;
  /** 警告状态色 */
  warning: string;
  /** 错误状态色 */
  error: string;
}

/**
 * 响应式断点配置
 */
export interface Breakpoints {
  /** 超小屏幕（手机）*/
  xs: number;
  /** 小屏幕（大手机）*/
  sm: number;
  /** 中等屏幕（平板）*/
  md: number;
  /** 大屏幕（桌面）*/
  lg: number;
  /** 超大屏幕（大桌面）*/
  xl: number;
}

/**
 * 全局主题配置接口
 */
export interface ThemeConfig {
  colors: ThemeColors;
  breakpoints: Breakpoints;
  fontFamily: {
    primary: string;
    mono: string;
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  boxShadow: {
    sm: string;
    md: string;
    lg: string;
  };
}

// ============ API 接口类型 ============

/**
 * 统一 API 响应格式
 */
export interface ApiResponse<T = unknown> {
  /** HTTP 状态码 */
  statusCode: number;
  /** 响应消息 */
  message: string;
  /** 数据负载 */
  data: T;
  /** 请求时间戳 */
  timestamp: string;
}

/**
 * 联系表单提交数据
 */
export interface ContactFormData {
  /** 姓名（必填，2-50 字符）*/
  name: string;
  /** 邮箱（必填，有效邮箱格式）*/
  email: string;
  /** 公司名称（可选）*/
  company?: string;
  /** 职位（可选）*/
  position?: string;
  /** 消息内容（必填，10-1000 字符）*/
  message: string;
  /** 感兴趣的业务领域 */
  interestAreas: string[];
}

/**
 * 联系表单验证错误
 */
export interface FormValidationError {
  field: keyof ContactFormData;
  message: string;
}

/**
 * 联系表单提交响应
 */
export interface ContactFormResponse {
  submissionId: string;
  receivedAt: string;
  estimatedResponseTime: string;
}

// ============ 产品特性数据类型 ============

/**
 * 产品特性项
 */
export interface FeatureItem {
  /** 特性唯一标识 */
  id: string;
  /** 特性标题 */
  title: string;
  /** 特性描述 */
  description: string;
  /** 图标名称 */
  icon: string;
  /** 特性列表 */
  capabilities: string[];
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
  trigger: string;
  /** 执行动作 */
  actions: string[];
  /** 场景图标 */
  icon: string;
}

/**
 * 支持的设备类型
 */
export interface DeviceType {
  /** 设备类型 ID */
  id: string;
  /** 设备类型名称 */
  name: string;
  /** 设备图标 */
  icon: string;
  /** 支持的功能 */
  features: string[];
}

// ============ 技术架构数据类型 ============

/**
 * 架构层级定义
 */
export interface ArchitectureLayer {
  /** 层级名称 */
  name: string;
  /** 层级描述 */
  description: string;
  /** 包含的组件 */
  components: ArchitectureComponent[];
  /** 层级颜色（用于可视化）*/
  color: string;
}

/**
 * 架构组件定义
 */
export interface ArchitectureComponent {
  /** 组件 ID */
  id: string;
  /** 组件名称 */
  name: string;
  /** 组件描述 */
  description: string;
  /** 技术栈 */
  technologies: string[];
  /** 是否支持交互式详情 */
  interactive: boolean;
  /** 详细文档链接 */
  docsUrl?: string;
}

/**
 * 技术架构图数据
 */
export interface ArchitectureDiagramData {
  layers: ArchitectureLayer[];
  connections: ArchitectureConnection[];
}

/**
 * 架构组件连接关系
 */
export interface ArchitectureConnection {
  /** 源组件 ID */
  from: string;
  /** 目标组件 ID */
  to: string;
  /** 连接类型 */
  type: 'data-flow' | 'api-call' | 'event' | 'dependency';
  /** 连接标签 */
  label?: string;
}

// ============ 组件 Props 接口 ============

/**
 * 导航栏组件 Props
 */
export interface NavbarProps {
  /** 是否固定在顶部 */
  fixed?: boolean;
  /** 导航链接列表 */
  links: NavLink[];
  /** Logo 文本 */
  logoText: string;
}

/**
 * 导航链接类型
 */
export interface NavLink {
  /** 链接文本 */
  label: string;
  /** 链接路径 */
  href: string;
  /** 是否外部链接 */
  external?: boolean;
}

/**
 * Hero 区域组件 Props
 */
export interface HeroSectionProps {
  /** 主标题 */
  title: string;
  /** 副标题 */
  subtitle: string;
  /** CTA 按钮文本 */
  ctaText: string;
  /** CTA 按钮链接 */
  ctaHref: string;
  /** 背景图片 URL（可选）*/
  backgroundImage?: string;
}

/**
 * 特性卡片组件 Props
 */
export interface FeatureCardProps {
  /** 特性数据 */
  feature: FeatureItem;
  /** 卡片是否可点击 */
  clickable?: boolean;
  /** 点击回调 */
  onClick?: (feature: FeatureItem) => void;
}

/**
 * 联系表单组件 Props
 */
export interface ContactFormProps {
  /** 表单提交处理函数 */
  onSubmit: (data: ContactFormData) => Promise<void>;
  /** 提交成功回调 */
  onSuccess?: (response: ContactFormResponse) => void;
  /** 提交失败回调 */
  onError?: (error: string) => void;
  /** 是否禁用表单 */
  disabled?: boolean;
}

/**
 * 表单输入字段配置
 */
export interface FormFieldConfig {
  /** 字段名称 */
  name: keyof ContactFormData;
  /** 字段标签 */
  label: string;
  /** 字段类型 */
  type: 'text' | 'email' | 'textarea' | 'select' | 'checkbox';
  /** 是否必填 */
  required: boolean;
  /** 占位符文本 */
  placeholder: string;
  /** 最小长度 */
  minLength?: number;
  /** 最大长度 */
  maxLength?: number;
  /** 验证正则表达式 */
  pattern?: RegExp;
  /** 自定义验证函数 */
  validate?: (value: string) => string | null;
  /** 选项列表（用于 select/checkbox）*/
  options?: { value: string; label: string }[];
}

/**
 * 页脚组件 Props
 */
export interface FooterProps {
  /** 公司名称 */
  companyName: string;
  /** 版权年份 */
  copyrightYear: number;
  /** 社交媒体链接 */
  socialLinks: SocialLink[];
  /** 快速链接 */
  quickLinks: NavLink[];
}

/**
 * 社交媒体链接
 */
export interface SocialLink {
  /** 平台名称 */
  platform: string;
  /** 链接 URL */
  url: string;
  /** 图标名称 */
  icon: string;
}

/**
 * 技术架构图组件 Props
 */
export interface ArchitectureDiagramProps {
  /** 架构图数据 */
  data: ArchitectureDiagramData;
  /** 是否启用交互模式 */
  interactive?: boolean;
  /** 组件点击回调 */
  onComponentClick?: (component: ArchitectureComponent) => void;
  /** 当前选中的组件 ID */
  selectedComponentId?: string;
}

// ============ 页面路由配置 ============

/**
 * 路由配置类型
 */
export interface RouteConfig {
  /** 路径 */
  path: string;
  /** 页面标题 */
  title: string;
  /** 页面组件名称 */
  component: string;
  /** 是否精确匹配 */
  exact?: boolean;
  /** 是否需要认证 */
  requiresAuth?: boolean;
}

// ============ 表单验证规则类型 ============

/**
 * 验证规则类型
 */
export type ValidationRule =
  | { type: 'required'; message: string }
  | { type: 'minLength'; value: number; message: string }
  | { type: 'maxLength'; value: number; message: string }
  | { type: 'pattern'; value: RegExp; message: string }
  | { type: 'email'; message: string }
  | { type: 'custom'; validator: (value: string) => boolean; message: string };

/**
 * 字段验证配置
 */
export interface FieldValidationConfig {
  /** 字段名称 */
  field: string;
  /** 验证规则列表 */
  rules: ValidationRule[];
}

// ============ 工具类型 ============

/**
 * 可选类型辅助
 */
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * 只读类型辅助
 */
export type ReadOnly<T> = {
  readonly [K in keyof T]: T[K];
};

/**
 * 深度只读类型辅助
 */
export type DeepReadOnly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadOnly<T[K]> : T[K];
};
