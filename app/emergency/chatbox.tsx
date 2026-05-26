import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { apiClient } from '@/services/apiClient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
    ActivityIndicator,
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

export default function ChatboxScreen() {
    const router = useRouter();
    const { t } = useTranslation();
    const flatListRef = useRef<FlatList>(null);

    const [messages, setMessages] = useState<Message[]>([
        { id: '1', text: t('chatbox_welcome'), sender: 'bot' },
    ]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSend = async () => {
        const cleanText = inputText.trim();
        if (!cleanText || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: cleanText,
            sender: 'user',
        };
        setMessages((prev) => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            const data = await apiClient.post<{
                success: boolean;
                response: string;
                language: string;
            }>('/api/v1/ai/text-query', {
                text: cleanText,
                context: '',
                language: 'en',
                rag_source: 'all',
            });

            const botMessage: Message = {
                id: (Date.now() + 1).toString(),
                text:
                    data.response ||
                    t('chatbox_no_answer'),
                sender: 'bot',
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            console.error('Chatbox API error:', error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: t('chatbox_network_error'),
                sender: 'bot',
            };
            setMessages((prev) => [...prev, errorMessage]);
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
            <StatusBar barStyle="dark-content" />
            <KeyboardAvoidingView
                style={styles.flex}
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
                {/* Header */}
                <View style={styles.header}>
                    <Pressable
                        onPress={() => router.back()}
                        style={styles.backBtn}
                        accessibilityRole="button"
                        accessibilityLabel="Go back"
                    >
                        <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
                    </Pressable>
                    <View style={styles.headerCenter}>
                        <Ionicons
                            name="chatbubbles"
                            size={rf(18)}
                            color={COLORS.primary}
                            style={styles.headerIcon}
                        />
                        <Text style={styles.headerTitle}>{t('chatbox_title')}</Text>
                    </View>
                    <View style={styles.headerSpacer} />
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
                        style={styles.textInput}
                        value={inputText}
                        onChangeText={setInputText}
                        placeholder={t('chatbox_placeholder')}
                        placeholderTextColor={COLORS.muted}
                        multiline
                        editable={!isLoading}
                    />
                    <Pressable
                        style={[
                            styles.sendButton,
                            (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
                        ]}
                        onPress={handleSend}
                        disabled={!inputText.trim() || isLoading}
                        accessibilityRole="button"
                        accessibilityLabel={t('chatbox_send')}
                    >
                        {isLoading ? (
                            <ActivityIndicator size="small" color="#fff" />
                        ) : (
                            <Ionicons name="send" size={rf(20)} color="#fff" />
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
        backgroundColor: COLORS.background,
    },
    flex: {
        flex: 1,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: SPACING.m,
        paddingVertical: SPACING.m,
        backgroundColor: COLORS.card,
        borderBottomWidth: 1,
        borderBottomColor: COLORS.border,
        ...SHADOWS.light,
    },
    backBtn: {
        padding: SPACING.xs,
        marginRight: SPACING.s,
    },
    headerCenter: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
    },
    headerIcon: {
        marginRight: SPACING.s,
    },
    headerTitle: {
        fontSize: rf(17),
        fontWeight: '700',
        color: COLORS.text,
    },
    headerSpacer: {
        width: rf(32),
    },
    listContent: {
        padding: SPACING.m,
        paddingBottom: SPACING.l,
        flexGrow: 1,
    },
    messageBubble: {
        marginVertical: SPACING.xs,
        paddingVertical: SPACING.m,
        paddingHorizontal: SPACING.m,
        borderRadius: RADIUS.m,
        maxWidth: '82%',
    },
    userBubble: {
        backgroundColor: COLORS.primary,
        alignSelf: 'flex-end',
        borderBottomRightRadius: RADIUS.s,
    },
    botBubble: {
        backgroundColor: COLORS.card,
        alignSelf: 'flex-start',
        borderBottomLeftRadius: RADIUS.s,
        borderWidth: 1,
        borderColor: COLORS.border,
    },
    userText: {
        color: '#fff',
        fontSize: rf(15),
        lineHeight: rf(22),
    },
    botText: {
        color: COLORS.text,
        fontSize: rf(15),
        lineHeight: rf(22),
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        padding: SPACING.m,
        backgroundColor: COLORS.card,
        borderTopWidth: 1,
        borderTopColor: COLORS.border,
    },
    textInput: {
        flex: 1,
        minHeight: rf(44),
        maxHeight: rf(100),
        borderWidth: 1,
        borderColor: COLORS.border,
        borderRadius: RADIUS.full,
        paddingHorizontal: SPACING.m,
        paddingVertical: SPACING.s,
        backgroundColor: COLORS.background,
        fontSize: rf(15),
        color: COLORS.text,
    },
    sendButton: {
        width: rf(44),
        height: rf(44),
        borderRadius: rf(22),
        backgroundColor: COLORS.primary,
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: SPACING.s,
        ...SHADOWS.light,
    },
    sendButtonDisabled: {
        backgroundColor: COLORS.border,
    },
});
