import { fn } from '@storybook/test';

import * as actual from './useUserPreferences';

export interface UserPreferences extends actual.UserPreferences {}
export interface UseUserPreferencesReturn extends actual.UseUserPreferencesReturn {}
export interface UserPreferencesContext extends actual.UserPreferencesContextType {}
export interface UserPreferencesProviderProps extends actual.UserPreferencesProviderProps {}


export const useUserPreferences = fn(actual.useUserPreferences).mockName('useUserPreferences');
export const UserPreferencesProvider = actual.UserPreferencesProvider;

export type Theme = actual.Theme;


export const SafeStorage = actual.SafeStorage;