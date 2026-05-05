/**
 * Mock调试面板
 * 提供mock模式的快速控制和状态查看
 */

import React, { useState, useEffect } from 'react';
import { Bug, Square, RotateCcw, List } from 'lucide-react';
import mockService from '../services/mock';

export function MockDebugPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [status, setStatus] = useState(mockService.status);

  useEffect(() => {
    const interval = setInterval(() => {
      setStatus(mockService.status);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const toggleMock = () => {
    const enabled = mockService.toggle();
    setStatus(mockService.status);
    console.log(`[Mock] ${enabled ? '启用' : '禁用'}mock模式`);
  };

  const testScenario = (scenarioId: string) => {
    const scenario = mockService.scenarios.find(s => s.id === scenarioId);
    if (scenario) {
      console.log(`[Mock] 测试场景: ${scenario.name}`);
      // 这里可以添加触发测试场景的逻辑
    }
  };

  if (!import.meta.env.DEV) {
    return null; // 生产环境不显示
  }

  return (
    <>
      {/* 悬浮按钮 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-4 right-4 z-50 bg-purple-600 hover:bg-purple-700 text-white p-3 rounded-full shadow-lg transition-all duration-200 flex items-center gap-2"
        title="Mock调试面板"
      >
        <Bug size={20} />
        {status.enabled && (
          <span className="bg-green-500 text-white text-xs px-1 rounded-full">ON</span>
        )}
      </button>

      {/* 调试面板 */}
      {isOpen && (
        <div className="fixed bottom-20 right-4 z-50 bg-white border border-gray-200 rounded-lg shadow-xl p-4 w-80 max-h-96 overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Bug size={16} />
              Mock调试面板
            </h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <Square size={16} />
            </button>
          </div>

          {/* 状态信息 */}
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="text-xs text-gray-600 mb-2">当前状态:</div>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${status.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
              <span className="text-sm font-medium">
                Mock模式: {status.enabled ? '已启用' : '已禁用'}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              已加载 {status.scenarios.length} 个场景
            </div>
          </div>

          {/* 控制按钮 */}
          <div className="mb-4">
            <button
              onClick={toggleMock}
              className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                status.enabled
                  ? 'bg-red-100 text-red-700 hover:bg-red-200'
                  : 'bg-green-100 text-green-700 hover:bg-green-200'
              }`}
            >
              <RotateCcw size={14} />
              {status.enabled ? '禁用Mock' : '启用Mock'}
            </button>
          </div>

          {/* 场景列表 */}
          <div className="mb-4">
            <div className="text-xs text-gray-600 mb-2 flex items-center gap-1">
              <List size={12} />
              测试场景:
            </div>
            <div className="space-y-2">
              {status.scenarios.map((scenarioName, index) => {
                const scenario = mockService.scenarios[index];
                return (
                  <button
                    key={scenario.id}
                    onClick={() => testScenario(scenario.id)}
                    className="w-full text-left p-2 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 rounded transition-colors"
                    title={scenario.userInput}
                  >
                    <div className="font-medium">{scenario.name}</div>
                    <div className="text-blue-600 truncate">
                      "{scenario.userInput}"
                    </div>
                    <div className="text-blue-500">
                      {scenario.events.length} 个事件
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 快速操作 */}
          <div className="border-t pt-3">
            <div className="text-xs text-gray-500 mb-2">快速操作:</div>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => {
                  mockService.debug.status();
                  console.log('[Mock] 已输出状态到控制台');
                }}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
              >
                查看状态
              </button>
              <button
                onClick={() => {
                  mockService.debug.listScenarios();
                  console.log('[Mock] 已输出场景列表到控制台');
                }}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
              >
                列出场景
              </button>
            </div>
          </div>

          {/* 提示信息 */}
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
            💡 这是开发调试工具，生产环境不会显示
          </div>
        </div>
      )}
    </>
  );
}