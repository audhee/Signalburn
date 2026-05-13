declare module 'expo-image-picker' {
  export const MediaTypeOptions: {
    Images: string;
    Videos: string;
    All: string;
  };
  
  export function requestCameraPermissionsAsync(): Promise<{ status: string }>;
  export function requestMediaLibraryPermissionsAsync(): Promise<{ status: string }>;
  
  export function launchCameraAsync(options?: any): Promise<{
    canceled: boolean;
    assets?: Array<{
      uri: string;
      type?: string;
      fileName?: string;
    }>;
  }>;
  
  export function launchImageLibraryAsync(options?: any): Promise<{
    canceled: boolean;
    assets?: Array<{
      uri: string;
      type?: string;
      fileName?: string;
    }>;
  }>;
}