import { fireEvent, render } from '@testing-library/react-native';
import React from 'react';
import EmergencyContacts from '../app/setup/contacts';
import ProfileSetup from '../app/setup/profile';

jest.mock('expo-router', () => ({
    useRouter: () => ({ push: jest.fn(), back: jest.fn() }),
}));
jest.mock('react-i18next', () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

describe('Validation Logic', () => {
    it('prevents profile save if name or age is missing', async () => {
        const { getAllByText } = render(<ProfileSetup />);
        const continueButton = getAllByText('save_profile')[0];

        fireEvent.press(continueButton);
        const errors = getAllByText('enter your full details correctly');
        expect(errors.length).toBeGreaterThanOrEqual(1);
    });

    it('triggers error as soon as numbers are typed in name section', () => {
        const { getByPlaceholderText, getByText } = render(<ProfileSetup />);
        const nameInput = getByPlaceholderText('name_placeholder');

        fireEvent.changeText(nameInput, 'Raj123');
        expect(getByText('enter proper credential')).toBeTruthy();
    });

    it('triggers error as soon as letters are typed in age section', () => {
        const { getByPlaceholderText, getByText } = render(<ProfileSetup />);
        const ageInput = getByPlaceholderText('age_placeholder');

        fireEvent.changeText(ageInput, '4abc');
        expect(getByText('enter age in numbers')).toBeTruthy();
    });

    it('prevents contact save if phone is not exactly 10 digits', async () => {
        const { getByText, getByPlaceholderText } = render(<EmergencyContacts />);
        const addBtn = getByText('+ Add Contact');
        fireEvent.press(addBtn);

        const nameInput = getByPlaceholderText('e.g., Raj Kumar');
        const relationInput = getByPlaceholderText('e.g., Son / Daughter / Doctor');
        const ageInput = getByPlaceholderText('e.g., 45');
        const phoneInput = getByPlaceholderText('Phone number');
        const saveBtn = getByText('Save');

        fireEvent.changeText(nameInput, 'Test');
        fireEvent.changeText(relationInput, 'Family');
        fireEvent.changeText(ageInput, '45');
        fireEvent.changeText(phoneInput, '123'); // Too short
        fireEvent.press(saveBtn);

        expect(getByText('Please enter a valid phone number.')).toBeTruthy();
    });
});
