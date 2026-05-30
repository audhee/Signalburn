import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import { Alert } from 'react-native';
import EmergencyContacts from '../app/setup/contacts';
import ProfileSetup from '../app/setup/profile';

jest.mock('expo-router', () => ({
    useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
}));
jest.mock('react-i18next', () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));
jest.spyOn(Alert, 'alert');

describe('Validation Logic', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('prevents profile save if name is missing', async () => {
        const { getByText } = render(<ProfileSetup />);
        // useTranslation mock returns the key name
        const continueButton = getByText('save_profile');

        fireEvent.press(continueButton);
        expect(Alert.alert).toHaveBeenCalledWith('error', 'name_required');
    });

    it('prevents contact save if phone is not exactly 10 digits', async () => {
        const { getByText, getByPlaceholderText } = render(<EmergencyContacts />);
        // This one is hardcoded in contacts.tsx
        const addBtn = getByText('+ Add Contact');
        fireEvent.press(addBtn);

        const nameInput = getByPlaceholderText('e.g., Raj Kumar');
        const relationInput = getByPlaceholderText('e.g., Son / Daughter / Doctor');
        const phoneInput = getByPlaceholderText('Phone number');
        const saveBtn = getByText('Save');

        fireEvent.changeText(nameInput, 'Test');
        fireEvent.changeText(relationInput, 'Family');
        fireEvent.changeText(phoneInput, '123456789'); // 9 digits (invalid)
        fireEvent.press(saveBtn);

        expect(Alert.alert).toHaveBeenCalledWith('Invalid phone', 'Please enter a 10-digit phone number.');
    });

    it('filters out numbers from name input in real-time', async () => {
        const { getByText, getByPlaceholderText } = render(<EmergencyContacts />);
        const addBtn = getByText('+ Add Contact');
        fireEvent.press(addBtn);

        const nameInput = getByPlaceholderText('e.g., Raj Kumar');
        fireEvent.changeText(nameInput, 'Test 123');
        expect(nameInput.props.value).toBe('Test ');
    });

    it('filters out numbers from relation input in real-time', async () => {
        const { getByText, getByPlaceholderText } = render(<EmergencyContacts />);
        const addBtn = getByText('+ Add Contact');
        fireEvent.press(addBtn);

        const relationInput = getByPlaceholderText('e.g., Son / Daughter / Doctor');
        fireEvent.changeText(relationInput, 'Family 456');
        expect(relationInput.props.value).toBe('Family ');
    });

    it('filters out non-digits and truncates phone input to 10 digits in real-time', async () => {
        const { getByText, getByPlaceholderText } = render(<EmergencyContacts />);
        const addBtn = getByText('+ Add Contact');
        fireEvent.press(addBtn);

        const phoneInput = getByPlaceholderText('Phone number');
        fireEvent.changeText(phoneInput, '+123-456 abc 789012');
        expect(phoneInput.props.value).toBe('1234567890');
    });

    it('filters out numbers from profile name input in real-time', async () => {
        const { getByPlaceholderText } = render(<ProfileSetup />);
        const nameInput = getByPlaceholderText('name_placeholder');
        fireEvent.changeText(nameInput, 'John 123');
        expect(nameInput.props.value).toBe('John ');
    });

    it('filters out non-digits from profile age input in real-time', async () => {
        const { getByPlaceholderText } = render(<ProfileSetup />);
        const ageInput = getByPlaceholderText('age_placeholder');
        fireEvent.changeText(ageInput, '75a8');
        expect(ageInput.props.value).toBe('758');
    });

    it('filters out numbers from profile other conditions input in real-time', async () => {
        const { getByPlaceholderText } = render(<ProfileSetup />);
        const otherInput = getByPlaceholderText('other_condition_placeholder');
        fireEvent.changeText(otherInput, 'Condition 99');
        expect(otherInput.props.value).toBe('Condition ');
    });

    it('prevents profile save if age is greater than 100', async () => {
        const { getByText, getByPlaceholderText } = render(<ProfileSetup />);
        const nameInput = getByPlaceholderText('name_placeholder');
        const ageInput = getByPlaceholderText('age_placeholder');
        const continueButton = getByText('save_profile');

        fireEvent.changeText(nameInput, 'John');
        fireEvent.changeText(ageInput, '120');
        fireEvent.press(continueButton);

        expect(Alert.alert).toHaveBeenCalledWith('Invalid age', 'Age must be between 0 and 100.');
    });
});
