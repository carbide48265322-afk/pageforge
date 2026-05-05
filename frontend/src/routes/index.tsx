import { createRoute } from '@tanstack/react-router';
import { rootRoute } from './__root';

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: IndexComponent,
});

function IndexComponent() {
  const handleSubmit = () => {
    window.location.href = `/chat/${Date.now()}`;
  };

  const templates = [
    { title: '上传数据，生成可视化PPT', icon: '📊' },
    { title: '上传 Excel，生成可交互的网页 DEMO', icon: '📈' },
    { title: '上传 PPT 课件，生成在线演示网页', icon: '🎤' },
    { title: '上传个人简历，生成个人网站', icon: '👤' },
  ];

  const categories = [
    { name: '文件处理', active: true },
    { name: '官网门户', active: false },
    { name: '创意游戏', active: false },
    { name: '效率工具', active: false },
    { name: 'AI 应用', active: false },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            思维未竟之处，<span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">秒悟</span>已然成真
          </h1>
          <p className="text-gray-500 text-lg">
            描述你想创作的桌面端页面，@使用技能...
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 p-2 mb-8">
          <div className="flex gap-2 mb-4">
            <button className="px-4 py-2 bg-black text-white rounded-lg text-sm font-medium">
              网页应用
            </button>
            <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium">
              H5应用
            </button>
            <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium">
              技能创建
            </button>
          </div>

          <div className="relative">
            <textarea
              className="w-full px-4 py-4 text-gray-800 bg-gray-50 rounded-xl border-none resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
              rows={3}
              placeholder="描述你想创作的桌面端页面，@使用技能..."
            />
            <div className="absolute right-4 bottom-4 flex items-center gap-3">
              <span className="text-sm text-gray-400">Swarms</span>
              <button
                onClick={handleSubmit}
                className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 transition-all hover:scale-105"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 19V5"/>
                  <path d="M5 12l7-7 7 7"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {categories.map((cat) => (
            <button
              key={cat.name}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                cat.active
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {templates.map((template, index) => (
            <button
              key={index}
              onClick={handleSubmit}
              className="group bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-gray-100 hover:border-gray-200 hover:shadow-lg transition-all hover:-translate-y-1 text-left"
            >
              <div className="text-3xl mb-3">{template.icon}</div>
              <p className="text-sm text-gray-700 font-medium">{template.title}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
