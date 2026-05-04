/**
 * File Event 处理器
 * 处理 file_created / file_updated / file_deleted 事件
 */

import type { FileNode } from '../types';

// 文件树状态（简单实现，实际可能用更复杂的树操作）
let fileTree: FileNode[] = [];

export const fileEventHandler = {
  /**
   * 处理 file_created 事件
   */
  onCreate(data: FileNode): FileNode[] {
    fileTree = appendFileNode(fileTree, data);
    return fileTree;
  },

  /**
   * 处理 file_updated 事件
   */
  onUpdate(data: FileNode): FileNode[] {
    fileTree = updateFileNode(fileTree, data);
    return fileTree;
  },

  /**
   * 处理 file_deleted 事件
   */
  onDelete(data: { path: string }): FileNode[] {
    fileTree = removeFileNode(fileTree, data.path);
    return fileTree;
  },

  /**
   * 获取当前文件树
   */
  getFileTree(): FileNode[] {
    return fileTree;
  },

  /**
   * 重置状态
   */
  reset(): void {
    fileTree = [];
  },
};

// ========== 辅助函数 ==========

function appendFileNode(tree: FileNode[], newNode: FileNode): FileNode[] {
  const newTree = [...tree];

  if (newNode.type === 'folder' && newNode.children) {
    // 如果是文件夹，直接添加
    newTree.push(newNode);
  } else {
    // 文件类型，需要找到对应的父文件夹
    const parts = newNode.path.split('/');
    if (parts.length > 1) {
      const parentPath = parts.slice(0, -1).join('/');
      const parent = findNode(newTree, parentPath);
      if (parent && parent.children) {
        parent.children.push(newNode);
      } else {
        // 父文件夹不存在，创建嵌套结构
        newTree.push(newNode);
      }
    } else {
      newTree.push(newNode);
    }
  }

  return newTree;
}

function updateFileNode(tree: FileNode[], updatedNode: FileNode): FileNode[] {
  return tree.map(node => {
    if (node.path === updatedNode.path) {
      return { ...node, ...updatedNode };
    }
    if (node.children) {
      return {
        ...node,
        children: updateFileNode(node.children, updatedNode),
      };
    }
    return node;
  });
}

function removeFileNode(tree: FileNode[], path: string): FileNode[] {
  return tree.filter(node => {
    if (node.path === path) {
      return false;
    }
    if (node.children) {
      node.children = removeFileNode(node.children, path);
    }
    return true;
  });
}

function findNode(tree: FileNode[], path: string): FileNode | null {
  for (const node of tree) {
    if (node.path === path) {
      return node;
    }
    if (node.children) {
      const found = findNode(node.children, path);
      if (found) return found;
    }
  }
  return null;
}
