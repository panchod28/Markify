import { create } from 'zustand';
import type { PreviewViewMode } from '@/types';

interface PreviewStore {
  selectedFileId: string | null;
  viewMode: PreviewViewMode;

  selectFile: (id: string) => void;
  toggleViewMode: () => void;
  reset: () => void;
}

export const usePreviewStore = create<PreviewStore>((set) => ({
  selectedFileId: null,
  viewMode: 'rendered',

  selectFile: (id) => set({ selectedFileId: id }),

  toggleViewMode: () => set(state => ({
    viewMode: state.viewMode === 'rendered' ? 'raw' : 'rendered',
  })),

  reset: () => set({ selectedFileId: null, viewMode: 'rendered' }),
}));
