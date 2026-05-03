// WebContainer API 类型声明
// 基于 StackBlitz WebContainer API 文档

declare module '*.css' {
  const content: string;
  export default content;
}

declare module '@webcontainer/api' {
  export interface FileSystemTree {
    [name: string]: FileSystemTree | string;
  }

  export interface WebContainer {
    fs: {
      mkdir(path: string, options?: { recursive?: boolean }): Promise<void>;
      writeFile(path: string, content: string): Promise<void>;
      readFile(path: string): Promise<string>;
      readdir(path: string): Promise<string[]>;
    };

    spawn(command: string, args: string[], options?: any): Promise<WebContainerProcess>;

    port: {
      waitForPort(port: number): Promise<string>;
    };

    mount(iframe: HTMLIFrameElement): Promise<void>;
    teardown(): Promise<void>;
  }

  export interface WebContainerProcess {
    output: ReadableStream<string>;
    exit: Promise<number>;
  }

  export const WebContainer: {
    boot(): Promise<WebContainer>;
  };
}