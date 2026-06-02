import { StorageService } from '@/services/storage';
import { create } from 'zustand';

type EmergencyState = {
    active: boolean;
    startEmergency: () => void;
    endEmergency: () => void;
    contacts: any[];
    loadContacts: () => Promise<void>;
};

export const useEmergencyStore = create<EmergencyState>((set) => ({
    active: false,
    contacts: [],
    startEmergency: () => set({ active: true }),
    endEmergency: () => set({ active: false }),
    loadContacts: async () => {
        const contacts = await StorageService.getEmergencyContacts();
        set({ contacts });
    }
}));
