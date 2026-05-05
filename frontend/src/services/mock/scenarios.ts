/**
 * Mock数据场景定义
 * 预设典型对话流程的mock数据
 */

export interface MockEvent {
  type: string;
  delay: number; // 延迟时间(ms)
  data: any;
}

export interface MockScenario {
  id: string;
  name: string;
  userInput: string;
  events: MockEvent[];
}

/**
 * React组件生成场景
 * 完整模拟：意图识别 → 思维链 → 计划 → 代码生成 → 回复
 */
export const reactComponentScenario: MockScenario = {
  id: 'react-component',
  name: 'React组件生成',
  userInput: '帮我创建一个计数器组件，要有增加、减少和重置功能',
  events: [
    // 1. 意图识别
    {
      type: 'intent:result',
      delay: 300,
      data: {
        intent: 'code_gen',
        confidence: 0.95,
        tags: ['react', 'component', 'counter'],
        mode: 'frontend',
        complexity: 'simple',
        suggested_style: 'modern'
      }
    },

    // 2. 思维链开始
    {
      type: 'thinking:start',
      delay: 500,
      data: { id: 'thinking_1' }
    },

    // 3. 思维链流式输出
    {
      type: 'thinking:delta',
      delay: 800,
      data: {
        id: 'thinking_1',
        content: '用户想要创建一个计数器组件，需要分析需求...'
      }
    },
    {
      type: 'thinking:delta',
      delay: 1200,
      data: {
        id: 'thinking_1',
        content: '需要三个功能：增加、减少、重置。使用React Hooks实现，包括useState管理计数状态。'
      }
    },
    {
      type: 'thinking:delta',
      delay: 1500,
      data: {
        id: 'thinking_1',
        content: '还需要考虑样式设计，使用现代化的UI风格。'
      }
    },

    // 4. 思维链结束
    {
      type: 'thinking:end',
      delay: 1800,
      data: {
        id: 'thinking_1',
        content: '分析完成，现在制定具体实现计划。'
      }
    },

    // 5. 计划开始
    {
      type: 'plan:start',
      delay: 2000,
      data: { id: 'plan_1' }
    },

    // 6. 计划步骤
    {
      type: 'plan:update',
      delay: 2300,
      data: {
        id: 'plan_1',
        steps: [
          { id: 1, label: '创建Counter组件文件', status: 'pending' },
          { id: 2, label: '实现useState状态管理', status: 'pending' },
          { id: 3, label: '添加三个操作按钮', status: 'pending' },
          { id: 4, label: '应用现代化样式', status: 'pending' },
          { id: 5, label: '启动开发服务器', status: 'pending' }
        ],
        isComplete: false
      }
    },

    // 7. 风格选择
    {
      type: 'style:selected',
      delay: 2600,
      data: {
        style: 'modern',
        primary_color: '#3b82f6',
        description: '现代化蓝色主题，圆角设计，渐变背景'
      }
    },

    // 8. 工具调用 - 创建项目
    {
      type: 'tool_call:start',
      delay: 3000,
      data: {
        tool_id: 'tool_1',
        name: 'write_file',
        input: {
          path: '/src/Counter.tsx',
          content: '// Counter组件内容'
        }
      }
    },

    // 9. 文件创建事件
    {
      type: 'file:created',
      delay: 3500,
      data: {
        file_path: '/src/Counter.tsx',
        name: 'Counter.tsx',
        language: 'typescript',
        size_bytes: 1024
      }
    },

    // 10. 工具调用完成
    {
      type: 'tool_call:end',
      delay: 4000,
      data: {
        tool_id: 'tool_1',
        status: 'success',
        durationMs: 1000
      }
    },

    // 11. 安装依赖
    {
      type: 'status:installing',
      delay: 4500,
      data: {
        status: 'installing',
        message: '正在安装项目依赖...'
      }
    },

    // 12. 安装完成
    {
      type: 'status:install_done',
      delay: 6000,
      data: {
        status: 'install_done',
        message: '依赖安装完成'
      }
    },

    // 13. 生成完成
    {
      type: 'status:generation_done',
      delay: 6500,
      data: {
        status: 'generation_done',
        message: '代码生成已完成'
      }
    },

    // 14. 启动开发服务器
    {
      type: 'status:starting_dev',
      delay: 7000,
      data: {
        status: 'starting_dev',
        message: '正在启动开发服务器...'
      }
    },

    // 15. 预览就绪
    {
      type: 'status:preview_ready',
      delay: 9000,
      data: {
        status: 'preview_ready',
        message: '预览已就绪',
        url: 'http://localhost:6001'
      }
    },

    // 16. 文本回复
    {
      type: 'text:delta',
      delay: 9500,
      data: {
        content: '✅ 已成功创建计数器组件！'
      }
    },
    {
      type: 'text:delta',
      delay: 9800,
      data: {
        content: '我为您生成了一个功能完整的React计数器组件，包含增加、减少和重置功能。预览窗口已经启动，您可以实时查看效果。'
      }
    },

    // 17. 文本完成
    {
      type: 'text:done',
      delay: 10000,
      data: {}
    }
  ]
};

/**
 * 简单聊天场景
 */
export const chatScenario: MockScenario = {
  id: 'simple-chat',
  name: '简单聊天',
  userInput: '你好，能帮我做什么？',
  events: [
    {
      type: 'intent:result',
      delay: 200,
      data: {
        intent: 'chat',
        confidence: 0.98
      }
    },
    {
      type: 'text:delta',
      delay: 500,
      data: {
        content: '你好！我是PageForge，一个AI驱动的代码生成平台。我可以帮你：'
      }
    },
    {
      type: 'text:delta',
      delay: 800,
      data: {
        content: '\n\n- 🎨 生成React组件和页面\n- 📱 创建HTML页面\n- 🔧 修改现有代码\n- 💡 解答技术问题'
      }
    },
    {
      type: 'text:done',
      delay: 1200,
      data: {}
    }
  ]
};

/**
 * 所有可用场景
 */
export const mockScenarios: MockScenario[] = [
  reactComponentScenario,
  chatScenario
];