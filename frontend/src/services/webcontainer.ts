/**
 * WebContainer 服务
 * 管理浏览器中的项目运行环境
 */

export interface WebContainerFile {
  path: string;
  content: string;
}

export interface WebContainerFolder {
  path: string;
  isDir: true;
}

export type WebContainerItem = WebContainerFile | WebContainerFolder;

export interface WebContainerProject {
  files: WebContainerFile[];
  dependencies?: Record<string, string>;
  scripts?: Record<string, string>;
}

/**
 * WebContainer 管理器
 * 使用 StackBlitz WebContainer API 在浏览器中运行项目
 */
export class WebContainerManager {
  private static instance: WebContainerManager;
  private container: any = null;
  private isReady = false;
  private iframe: HTMLIFrameElement | null = null;

  private constructor() {}

  static getInstance(): WebContainerManager {
    if (!WebContainerManager.instance) {
      WebContainerManager.instance = new WebContainerManager();
    }
    return WebContainerManager.instance;
  }

  /**
   * 初始化 WebContainer
   */
  async initialize(containerElement: HTMLElement): Promise<void> {
    if (this.isReady) return;

    try {
      // 动态导入 WebContainer
      // TODO: 安装 @webcontainer/api 包后取消注释
      // const { WebContainer } = await import('@webcontainer/api');

      // 创建 iframe 容器
      this.iframe = document.createElement('iframe');
      this.iframe.className = 'w-full h-full border-0';
      this.iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
      containerElement.appendChild(this.iframe);

      // 启动 WebContainer
      // TODO: 实现实际的 WebContainer 启动逻辑
      this.container = null; // 临时模拟
      this.isReady = true;

      console.log('WebContainer 初始化成功');
    } catch (error) {
      console.error('WebContainer 初始化失败:', error);
      throw new Error('WebContainer 初始化失败，请检查网络连接');
    }
  }

  /**
   * 创建项目文件结构
   */
  async createProject(project: WebContainerProject): Promise<void> {
    if (!this.container || !this.isReady) {
      throw new Error('WebContainer 未初始化');
    }

    try {
      // 写入文件
      for (const file of project.files) {
        // 确保目录存在
        const dirPath = file.path.split('/').slice(0, -1).join('/');
        if (dirPath) {
          await this.container.fs.mkdir(dirPath, { recursive: true });
        }

        // 写入文件内容
        await this.container.fs.writeFile(file.path, file.content);
      }

      // 创建 package.json
      if (project.dependencies || project.scripts) {
        const packageJson = {
          name: 'generated-project',
          version: '1.0.0',
          type: 'module',
          scripts: project.scripts || {
            dev: 'vite',
            build: 'vite build',
            preview: 'vite preview'
          },
          dependencies: project.dependencies || {},
          devDependencies: {
            'vite': '^5.0.0'
          }
        };

        await this.container.fs.writeFile('/package.json', JSON.stringify(packageJson, null, 2));
      }

      console.log('项目文件创建完成');
    } catch (error) {
      console.error('创建项目失败:', error);
      throw error;
    }
  }

  /**
   * 安装依赖
   */
  async installDependencies(): Promise<void> {
    if (!this.container || !this.isReady) {
      throw new Error('WebContainer 未初始化');
    }

    try {
      // 安装依赖
      const installProcess = await this.container.spawn('npm', ['install']);

      // 监听安装输出
      installProcess.output.pipeTo(
        new WritableStream({
          write(chunk) {
            console.log('npm install:', chunk);
          }
        })
      );

      // 等待安装完成
      const installExitCode = await installProcess.exit;
      if (installExitCode !== 0) {
        throw new Error('依赖安装失败');
      }

      console.log('依赖安装完成');
    } catch (error) {
      console.error('安装依赖失败:', error);
      throw error;
    }
  }

  /**
   * 启动开发服务器
   */
  async startDevServer(): Promise<string> {
    if (!this.container || !this.isReady) {
      throw new Error('WebContainer 未初始化');
    }

    try {
      // 启动开发服务器
      const devProcess = await this.container.spawn('npm', ['run', 'dev']);

      // 监听服务器输出
      devProcess.output.pipeTo(
        new WritableStream({
          write(chunk) {
            console.log('dev server:', chunk);
          }
        })
      );

      // 等待服务器准备就绪
      const serverUrl = await this.container.port.waitForPort(6000);

      // 将服务器连接到 iframe
      if (this.iframe) {
        await this.container.mount(this.iframe);
      }

      console.log('开发服务器启动成功:', serverUrl);
      return serverUrl;
    } catch (error) {
      console.error('启动开发服务器失败:', error);
      throw error;
    }
  }

  /**
   * 从 HTML 字符串创建项目
   */
  createProjectFromHtml(html: string): WebContainerProject {
    // 解析 HTML，提取 CSS 和 JS
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // 提取样式
    const styles = Array.from(doc.querySelectorAll('style'))
      .map(style => style.textContent || '')
      .join('\n');

    // 提取脚本
    const scripts = Array.from(doc.querySelectorAll('script'))
      .map(script => script.textContent || '')
      .join('\n');

    // 移除样式和脚本，只保留结构
    doc.querySelectorAll('style, script').forEach(el => el.remove());

    const files: WebContainerFile[] = [
      {
        path: '/index.html',
        content: `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Page</title>
    <link rel="stylesheet" href="/src/style.css">
</head>
<body>
    ${doc.body.innerHTML}
    <script type="module" src="/src/main.js"></script>
</body>
</html>`
      }
    ];

    // 如果有样式，创建 CSS 文件
    if (styles.trim()) {
      files.push({
        path: '/src/style.css',
        content: styles
      });
    }

    // 如果有脚本，创建 JS 文件
    if (scripts.trim()) {
      files.push({
        path: '/src/main.js',
        content: scripts
      });
    }

    return {
      files,
      dependencies: {
        'react': '^19.0.0',
        'react-dom': '^19.0.0'
      },
      scripts: {
        dev: 'vite',
        build: 'vite build',
        preview: 'vite preview'
      }
    };
  }

  /**
   * 销毁 WebContainer
   */
  async destroy(): Promise<void> {
    if (this.container) {
      await this.container.teardown();
      this.container = null;
    }

    if (this.iframe && this.iframe.parentNode) {
      this.iframe.parentNode.removeChild(this.iframe);
      this.iframe = null;
    }

    this.isReady = false;
  }

  /**
   * 获取当前状态
   */
  getStatus(): { isReady: boolean; hasContainer: boolean; hasIframe: boolean } {
    return {
      isReady: this.isReady,
      hasContainer: !!this.container,
      hasIframe: !!this.iframe
    };
  }
}