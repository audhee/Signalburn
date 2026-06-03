import { API_BASE_URL } from '@/constants/api';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import React, { useState, useRef } from 'react';
import {
    ActivityIndicator,
    Keyboard,
    FlatList,
    KeyboardAvoidingView,
    Platform,
    Pressable,
    SafeAreaView,
    StatusBar,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';

type Message = {
    id: string;
    text: string;
    sender: 'user' | 'bot';
};

const API_ENDPOINT = `${API_BASE_URL}/api/v1/ai/text-query`;

export default function ChatboxScreen() {
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: '🌲 Arohan Trekker First-Aid Tracker active. State your emergency or symptoms (e.g., altitude sickness, muscle sprain, leech bite).',
            sender: 'bot',
        },
    ]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const flatListRef = useRef<FlatList>(null);

    const handleSend = async () => {
        const cleanText = inputText.trim();
        if (!cleanText || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: cleanText,
            sender: 'user',
        };
        setMessages((prev) => [...prev, userMessage]);
        const currentInput = cleanText;
        setInputText('');
        setIsLoading(true);
        Keyboard.dismiss();

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: currentInput,
                    context: '',
                    language: 'en',
                    rag_source: 'sashwat_optimized',
                }),
            });

            if (!response.ok) {
                const errorText = await response.text().catch(() => '');
                let detail = `Server error (${response.status})`;
                try {
                    const errJson = JSON.parse(errorText);
                    detail = errJson.detail || detail;
                } catch {}
                throw new Error(detail);
            }

            const data = await response.json();

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                text:
                    data.response ||
                    'Unable to retrieve medical guidelines. If severe, stop trekking and head to base camp immediately.',
                sender: 'bot',
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error: any) {
            console.error('Chatbox error:', error);
            const errorMsg =
                error.message?.includes('Network') ||
                error.message?.includes('fetch') ||
                error.message?.includes('Failed to fetch')
                    ? 'Network connection error. Check your connection and try again.'
                    : error.message || 'Something went wrong. Please try again.';
            setMessages((prev) => [
                ...prev,
                {
                    id: Date.now().toString(),
                    text: errorMsg,
                    sender: 'bot',
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const renderMessage = ({ item }: { item: Message }) => {
        const isUser = item.sender === 'user';
        return (
            <View
                style={[
                    styles.messageBubble,
                    isUser ? styles.userBubble : styles.botBubble,
                ]}
            >
                <Text style={isUser ? styles.userText : styles.botText}>
                    {item.text}
                </Text>
            </View>
        );
    };

    return (
        <SafeAreaView style={styles.safeArea}>
            <StatusBar barStyle="light-content" />
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={styles.flex}
            >
                {/* Header with Back Button */}
                <View style={styles.header}>
                    <Pressable
                        onPress={() => router.back()}
                        style={styles.backBtn}
                        accessibilityRole="button"
                        accessibilityLabel="Go back"
                    >
                        <Ionicons name="arrow-back" size={22} color="#fff" />
                    </Pressable>
                    <View style={styles.headerCenter}>
                        <Text style={styles.headerTitle}>⛰️ Arohan Trek Tracker</Text>
                        <Text style={styles.headerSubtitle}>First-Aid Emergency Assistant</Text>
                    </View>
                </View>

                {/* Messages */}
                <FlatList
                    ref={flatListRef}
                    data={messages}
                    keyExtractor={(item) => item.id}
                    renderItem={renderMessage}
                    contentContainerStyle={styles.listContent}
                    onContentSizeChange={() =>
                        flatListRef.current?.scrollToEnd({ animated: true })
                    }
                    showsVerticalScrollIndicator={false}
                />

                {/* Input */}
                <View style={styles.inputContainer}>
                    <TextInput
                        style={[styles.input, isLoading && styles.inputDisabled]}
                        value={inputText}
                        onChangeText={setInputText}
                        placeholder="Describe issue (e.g., pair mud gaya, sans phool rahi hai)..."
                        placeholderTextColor="#94a3b8"
                        editable={!isLoading}
                        multiline
                    />
                    <Pressable
                        style={[
                            styles.sendButton,
                            (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
                        ]}
                        onPress={handleSend}
                        disabled={!inputText.trim() || isLoading}
                        accessibilityRole="button"
                        accessibilityLabel="Send message"
                    >
                        {isLoading ? (
                            <ActivityIndicator size="small" color="#fff" />
                        ) : (
                            <Ionicons name="send" size={18} color="#fff" />
                        )}
                    </Pressable>
                </View>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    safeArea: {
        flex: 1,
        backgroundColor: '#1e3a1e',
    },
    flex: {
        flex: 1,
        backgroundColor: '#f4f6f0',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 12,
        paddingVertical: 12,
        backgroundColor: '#1e3a1e',
    },
    backBtn: {
        padding: 4,
        marginRight: 8,
    },
    headerCenter: {
        flex: 1,
    },
    headerTitle: {
        color: '#fff',
        fontSize: 17,
        fontWeight: 'bold',
    },
    headerSubtitle: {
        color: '#a3e635',
        fontSize: 11,
        fontWeight: '500',
        marginTop: 1,
    },
    listContent: {
        padding: 12,
        paddingBottom: 16,
        flexGrow: 1,
    },
    messageBubble: {
        marginVertical: 5,
        paddingVertical: 12,
        paddingHorizontal: 14,
        borderRadius: 15,
        maxWidth: '85%',
    },
    userBubble: {
        backgroundColor: '#2f5233',
        alignSelf: 'flex-end',
        borderBottomRightRadius: 4,
    },
    botBubble: {
        backgroundColor: '#ffffff',
        alignSelf: 'flex-start',
        borderBottomLeftRadius: 4,
        borderWidth: 1,
        borderColor: '#e2e8f0',
    },
    userText: {
        color: '#fff',
        fontSize: 15,
        lineHeight: 21,
    },
    botText: {
        color: '#1e293b',
        fontSize: 15,
        lineHeight: 21,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        padding: 12,
        backgroundColor: '#fff',
        borderTopWidth: 1,
        borderColor: '#e2e8f0',
    },
    input: {
        flex: 1,
        minHeight: 42,
        maxHeight: 100,
        borderWidth: 1,
        borderColor: '#cbd5e1',
        borderRadius: 20,
        paddingHorizontal: 16,
        paddingVertical: 10,
        backgroundColor: '#f8fafc',
        fontSize: 15,
        color: '#1e293b',
    },
    inputDisabled: {
        backgroundColor: '#f1f5f9',
        opacity: 0.7,
    },
    sendButton: {
        width: 42,
        height: 42,
        borderRadius: 21,
        backgroundColor: '#1e3a1e',
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: 10,
    },
    sendButtonDisabled: {
        backgroundColor: '#94a3b8',
    },
});
