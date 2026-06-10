import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Platform,
  TextInput,
  Modal,
  ImageBackground,
  FlatList,
  Dimensions
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons, MaterialCommunityIcons, FontAwesome5 } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { COLORS, SPACING, RADIUS, SHADOWS } from '@/constants/theme';
import { rf } from '@/constants/responsive';
import { API_BASE_URL } from '@/constants/api';
import { apiClient } from '@/services/apiClient';

// Safe import for WebView
let WebView: any = null;
if (Platform.OS !== 'web') {
  try {
    WebView = require('react-native-webview').WebView;
  } catch (e) {
    console.warn("WebView module not found");
  }
}

const { width } = Dimensions.get('window');
const RAZORPAY_KEY_ID = process.env.EXPO_PUBLIC_RAZORPAY_KEY_ID || "rzp_test_SeaY2w7Oi54EJy";

const CATEGORIES = [
  { id: '1', name: 'Health', icon: 'medical-bag', color: '#FF5252' },
  { id: '2', name: 'Meds', icon: 'pill', color: '#448AFF' },
  { id: '3', name: 'Care', icon: 'hand-heart', color: '#4CAF50' },
  { id: '4', name: 'Devices', icon: 'watch-variant', color: '#FF9800' },
  { id: '5', name: 'Support', icon: 'phone-classic', color: '#9C27B0' },
];

const FEATURED_SERVICES = [
  {
    id: 'fs_1',
    name: 'Home Nurse Visit',
    desc: 'Professional nursing care at your doorstep.',
    price: '₹1200',
    icon: 'home-plus',
    color: '#E3F2FD',
    iconColor: '#1976D2'
  },
  {
    id: 'fs_2',
    name: 'Pharmacy Delivery',
    desc: 'Get your monthly medicines delivered.',
    price: '₹500/mo',
    icon: 'truck-delivery',
    color: '#F1F8E9',
    iconColor: '#388E3C'
  },
  {
    id: 'fs_3',
    name: 'Emergency Watch',
    desc: 'Smart wearable for fall detection.',
    price: '₹4999',
    icon: 'watch-vibrate',
    color: '#FFF3E0',
    iconColor: '#F57C00'
  }
];

export default function ShopScreen() {
  const router = useRouter();
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [rechargeAmount, setRechargeAmount] = useState('500');
  const [paying, setPaying] = useState(false);
  const [showWebView, setShowWebView] = useState(false);
  const [showRecharge, setShowRecharge] = useState(false);
  const [paymentData, setPaymentData] = useState<any>(null);
  const [balance, setBalance] = useState(750); // Mock balance

  useEffect(() => {
    apiClient.get('/api/v1/shop/services')
      .then(data => setServices(data))
      .catch(e => {
        console.error("Fetch services error:", e);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleRecharge = async () => {
    if (!rechargeAmount || isNaN(Number(rechargeAmount))) {
      Alert.alert("Error", "Please enter a valid amount");
      return;
    }

    setPaying(true);
    try {
      const orderData = await apiClient.post('/api/v1/shop/create-order', {
        amount: Number(rechargeAmount) * 100,
        currency: "INR"
      });

      if (!orderData.id) throw new Error(orderData.detail || "Order ID missing");

      setPaymentData(orderData);
      
      if (Platform.OS === 'web') {
        handleWebPayment(orderData);
      } else {
        setShowWebView(true);
      }
    } catch (error: any) {
      Alert.alert("Payment Error", error.message);
      setPaying(false);
    }
  };

  const handleWebPayment = (orderData: any) => {
    const options = {
      key: RAZORPAY_KEY_ID,
      amount: orderData.amount,
      currency: "INR",
      name: "Arohan Enterprise",
      order_id: orderData.id,
      handler: (res: any) => verifyPayment(res),
      prefill: { contact: '9999999999' },
      theme: { color: COLORS.primary },
      modal: { ondismiss: () => setPaying(false) }
    };

    if ((window as any).Razorpay) {
      const rzp = new (window as any).Razorpay(options);
      rzp.open();
    } else {
      Alert.alert("Error", "Razorpay SDK not loaded");
      setPaying(false);
    }
  };

  const verifyPayment = async (data: any) => {
    try {
      const result = await apiClient.post('/api/v1/shop/verify-payment', {
        razorpay_order_id: data.razorpay_order_id,
        razorpay_payment_id: data.razorpay_payment_id,
        razorpay_signature: data.razorpay_signature
      });
      
      if (result.status === "success") {
        setBalance(prev => prev + Number(rechargeAmount));
        Alert.alert("Success", "Recharge completed successfully!");
        setShowRecharge(false);
      } else {
        Alert.alert("Error", "Verification failed");
      }
    } catch (e: any) {
      Alert.alert("Error", "Could not verify payment");
    } finally {
      setPaying(false);
      setShowWebView(false);
    }
  };

  const html = paymentData ? `
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <style>
          body { 
            font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            display: flex; 
            flex-direction: column; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            background: #fff; 
          }
          .btn { 
            background: ${COLORS.primary}; 
            color: white; 
            padding: 15px 30px; 
            border: none; 
            border-radius: 12px; 
            font-weight: bold; 
            font-size: 18px; 
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
          }
          #log { margin-top: 20px; font-size: 14px; color: #666; text-align: center; width: 80%; }
          .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid ${COLORS.primary};
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 2s linear infinite;
            margin-bottom: 20px;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>
      </head>
      <body>
        <div id="loader" class="loader"></div>
        <button id="pay-btn" class="btn" style="display: none;">Pay ₹${Number(rechargeAmount)}</button>
        <div id="log">Initializing Secure Checkout...</div>
        <script>
          var options = {
            "key": "${RAZORPAY_KEY_ID}",
            "amount": "${paymentData.amount}",
            "currency": "INR",
            "name": "Arohan Enterprise",
            "order_id": "${paymentData.id}",
            "handler": function (res) { 
              window.ReactNativeWebView.postMessage(JSON.stringify({type:'success', data:res})); 
            },
            "prefill": {
              "contact": "9999999999"
            },
            "theme": { "color": "${COLORS.primary}" },
            "modal": { 
              "ondismiss": function() { 
                window.ReactNativeWebView.postMessage(JSON.stringify({type:'cancel'})); 
              } 
            }
          };

          function openRazorpay() {
            if (typeof Razorpay === 'undefined') {
              setTimeout(openRazorpay, 500);
              return;
            }
            document.getElementById('loader').style.display = 'none';
            document.getElementById('pay-btn').style.display = 'block';
            document.getElementById('log').innerHTML = 'Secure payment gateway ready.';
            
            var rzp = new Razorpay(options);
            rzp.on('payment.failed', function (response){
              window.ReactNativeWebView.postMessage(JSON.stringify({type:'error', data:response.error}));
            });
            rzp.open();
          }

          document.getElementById('pay-btn').onclick = function() {
            var rzp = new Razorpay(options);
            rzp.open();
          };

          window.onload = function() {
            setTimeout(openRazorpay, 1000);
          };
        </script>
      </body>
    </html>
  ` : '';

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Shop & Services</Text>
        <TouchableOpacity onPress={() => setShowRecharge(true)}>
          <Ionicons name="wallet-outline" size={rf(24)} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Wallet Banner */}
        <ImageBackground 
          source={{ uri: 'https://images.unsplash.com/photo-1550565118-3a14e8d0386f?q=80&w=2070&auto=format&fit=crop' }}
          style={styles.walletBanner}
          imageStyle={{ borderRadius: RADIUS.l }}
        >
          <View style={styles.overlay}>
            <Text style={styles.walletLabel}>Wallet Balance</Text>
            <Text style={styles.walletValue}>₹{balance}</Text>
            <TouchableOpacity style={styles.topUpBtn} onPress={() => setShowRecharge(true)}>
              <Text style={styles.topUpBtnText}>Quick Recharge</Text>
              <Ionicons name="add-circle" size={rf(18)} color="white" />
            </TouchableOpacity>
          </View>
        </ImageBackground>

        {/* Categories */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Categories</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.catScroll}>
          {CATEGORIES.map(cat => (
            <TouchableOpacity key={cat.id} style={styles.catItem}>
              <View style={[styles.catIconBox, { backgroundColor: cat.color + '20' }]}>
                <MaterialCommunityIcons name={cat.icon as any} size={rf(24)} color={cat.color} />
              </View>
              <Text style={styles.catLabel}>{cat.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* My Active Services */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>My Active Services</Text>
        </View>
        {loading ? <ActivityIndicator size="small" color={COLORS.primary} style={{ margin: SPACING.m }} /> : (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.activeScroll}>
            {services.length > 0 ? services.map(s => (
              <View key={s.id} style={styles.activeCard}>
                <View style={styles.activeIconCircle}>
                   <MaterialCommunityIcons name="check-circle" size={rf(20)} color={COLORS.success} />
                </View>
                <Text style={styles.activeTitle} numberOfLines={1}>{s.name}</Text>
                <Text style={styles.activeExpiry}>Exp: {s.expiry_date}</Text>
                <View style={styles.statusBadge}>
                   <Text style={styles.statusText}>{s.status}</Text>
                </View>
              </View>
            )) : (
              <View style={styles.emptyServices}>
                <Text style={styles.emptyText}>No active subscriptions yet.</Text>
              </View>
            )}
          </ScrollView>
        )}

        {/* Featured Services */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Explore New Services</Text>
        </View>
        {FEATURED_SERVICES.map(fs => (
          <TouchableOpacity key={fs.id} style={styles.featureCard}>
            <View style={[styles.featureIconBox, { backgroundColor: fs.color }]}>
              <MaterialCommunityIcons name={fs.icon as any} size={rf(32)} color={fs.iconColor} />
            </View>
            <View style={styles.featureInfo}>
              <Text style={styles.featureTitle}>{fs.name}</Text>
              <Text style={styles.featureDesc}>{fs.desc}</Text>
              <View style={styles.featurePriceRow}>
                <Text style={styles.featurePrice}>{fs.price}</Text>
                <View style={styles.buyBtn}>
                  <Text style={styles.buyBtnText}>Get Now</Text>
                </View>
              </View>
            </View>
          </TouchableOpacity>
        ))}
        
        <View style={{ height: SPACING.xxl }} />
      </ScrollView>

      {/* Recharge Modal */}
      <Modal visible={showRecharge} animationType="fade" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add Money</Text>
              <TouchableOpacity onPress={() => setShowRecharge(false)}>
                <Ionicons name="close" size={rf(24)} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            
            <Text style={styles.inputLabel}>Enter Amount (₹)</Text>
            <View style={styles.inputContainer}>
              <TextInput 
                style={styles.rechargeInput} 
                value={rechargeAmount} 
                onChangeText={setRechargeAmount} 
                keyboardType="numeric"
                autoFocus
              />
            </View>

            <View style={styles.presetContainer}>
              {['500', '1000', '2000'].map(amt => (
                <TouchableOpacity 
                  key={amt} 
                  style={[styles.presetBtn, rechargeAmount === amt && styles.presetBtnActive]}
                  onPress={() => setRechargeAmount(amt)}
                >
                  <Text style={[styles.presetText, rechargeAmount === amt && styles.presetTextActive]}>₹{amt}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <TouchableOpacity 
              style={[styles.payBtn, paying && { opacity: 0.7 }]} 
              onPress={handleRecharge}
              disabled={paying}
            >
              {paying ? <ActivityIndicator color="white" /> : (
                <>
                  <Text style={styles.payBtnText}>Proceed to Pay</Text>
                  <Ionicons name="shield-checkmark" size={rf(18)} color="white" style={{ marginLeft: 8 }} />
                </>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Payment WebView Modal */}
      {showWebView && WebView && paymentData && (
        <Modal visible={true} animationType="slide" onRequestClose={() => { setShowWebView(false); setPaying(false); }}>
          <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
            <View style={styles.webViewHeader}>
               <Text style={styles.webViewTitle}>Secure Razorpay Payment</Text>
               <TouchableOpacity onPress={() => { setShowWebView(false); setPaying(false); }}>
                 <Ionicons name="close" size={rf(24)} color={COLORS.error} />
               </TouchableOpacity>
            </View>
            <WebView 
              source={{ html }} 
              javaScriptEnabled={true}
              domStorageEnabled={true}
              originWhitelist={['*']}
              allowsInlineMediaPlayback={true}
              mixedContentMode="always"
              headers={{ 'ngrok-skip-browser-warning': 'true' }}
              onMessage={(e:any) => {
                try {
                  const res = JSON.parse(e.nativeEvent.data);
                  if (res.type === 'success') {
                    verifyPayment(res.data);
                  } else if (res.type === 'cancel' || res.type === 'error') {
                    setShowWebView(false);
                    setPaying(false);
                    if (res.type === 'error') {
                      Alert.alert("Payment Failed", res.data?.description || "An error occurred");
                    }
                  }
                } catch(err) { 
                  console.error("WebView Parse Error:", err); 
                }
              }}
              style={{ flex: 1 }}
            />
          </SafeAreaView>
        </Modal>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  header: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.l,
    paddingVertical: SPACING.m,
    backgroundColor: '#fff',
    ...SHADOWS.light
  },
  backBtn: { padding: 5 },
  headerTitle: { fontSize: rf(18), fontWeight: '800', color: COLORS.text },
  scrollContent: { padding: SPACING.l },
  
  walletBanner: {
    width: '100%',
    height: rf(140),
    marginBottom: SPACING.xl,
    overflow: 'hidden',
    borderRadius: RADIUS.l,
    ...SHADOWS.medium
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    padding: SPACING.l,
    justifyContent: 'center'
  },
  walletLabel: { color: 'rgba(255,255,255,0.8)', fontSize: rf(14), fontWeight: '600' },
  walletValue: { color: '#fff', fontSize: rf(32), fontWeight: '900', marginVertical: SPACING.xs },
  topUpBtn: { 
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.primary,
    alignSelf: 'flex-start',
    paddingHorizontal: SPACING.m,
    paddingVertical: SPACING.s,
    borderRadius: RADIUS.full,
    marginTop: SPACING.s
  },
  topUpBtnText: { color: '#fff', fontWeight: 'bold', fontSize: rf(12), marginRight: 5 },

  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: SPACING.m },
  sectionTitle: { fontSize: rf(16), fontWeight: '800', color: COLORS.text },
  
  catScroll: { marginBottom: SPACING.xl },
  catItem: { alignItems: 'center', marginRight: SPACING.l },
  catIconBox: { width: rf(56), height: rf(56), borderRadius: rf(28), alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.s },
  catLabel: { fontSize: rf(12), fontWeight: '600', color: COLORS.muted },

  activeScroll: { marginBottom: SPACING.xl },
  activeCard: { 
    width: width * 0.4, 
    backgroundColor: '#fff', 
    padding: SPACING.m, 
    borderRadius: RADIUS.m, 
    marginRight: SPACING.m,
    borderWidth: 1,
    borderColor: '#eee',
    ...SHADOWS.light
  },
  activeIconCircle: { marginBottom: SPACING.s },
  activeTitle: { fontSize: rf(14), fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  activeExpiry: { fontSize: rf(10), color: COLORS.muted, marginBottom: SPACING.s },
  statusBadge: { backgroundColor: '#E8F5E9', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 4, alignSelf: 'flex-start' },
  statusText: { color: '#2E7D32', fontSize: rf(10), fontWeight: '800' },
  emptyServices: { padding: SPACING.l, alignItems: 'center', width: width - SPACING.l * 2 },
  emptyText: { color: COLORS.muted, fontSize: rf(14) },

  featureCard: { 
    flexDirection: 'row', 
    backgroundColor: '#fff', 
    borderRadius: RADIUS.l, 
    padding: SPACING.m, 
    marginBottom: SPACING.m,
    borderWidth: 1,
    borderColor: '#f0f0f0',
    ...SHADOWS.light
  },
  featureIconBox: { width: rf(70), height: rf(70), borderRadius: RADIUS.m, alignItems: 'center', justifyContent: 'center', marginRight: SPACING.m },
  featureInfo: { flex: 1 },
  featureTitle: { fontSize: rf(15), fontWeight: '800', color: COLORS.text, marginBottom: 4 },
  featureDesc: { fontSize: rf(12), color: COLORS.muted, marginBottom: SPACING.m },
  featurePriceRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  featurePrice: { fontSize: rf(16), fontWeight: '900', color: COLORS.primary },
  buyBtn: { backgroundColor: COLORS.primary + '15', paddingHorizontal: 12, paddingVertical: 6, borderRadius: RADIUS.s },
  buyBtnText: { color: COLORS.primary, fontWeight: '800', fontSize: rf(11) },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: '#fff', borderTopLeftRadius: RADIUS.xl, borderTopRightRadius: RADIUS.xl, padding: SPACING.xl },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: SPACING.l },
  modalTitle: { fontSize: rf(20), fontWeight: '800' },
  inputLabel: { fontSize: rf(14), color: COLORS.muted, marginBottom: SPACING.s },
  inputContainer: { backgroundColor: '#f5f5f5', borderRadius: RADIUS.m, padding: SPACING.m, marginBottom: SPACING.l },
  rechargeInput: { fontSize: rf(24), fontWeight: '900', color: COLORS.text },
  presetContainer: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: SPACING.xl },
  presetBtn: { flex: 1, paddingVertical: 12, alignItems: 'center', borderRadius: RADIUS.m, borderWidth: 1, borderColor: '#ddd', marginHorizontal: 4 },
  presetBtnActive: { borderColor: COLORS.primary, backgroundColor: COLORS.primary + '10' },
  presetText: { fontWeight: '700', color: COLORS.muted },
  presetTextActive: { color: COLORS.primary },
  payBtn: { backgroundColor: COLORS.primary, padding: SPACING.l, borderRadius: RADIUS.m, alignItems: 'center', flexDirection: 'row', justifyContent: 'center', ...SHADOWS.medium },
  payBtnText: { color: '#fff', fontWeight: '800', fontSize: rf(16) },

  webViewHeader: { padding: 15, borderBottomWidth: 1, borderBottomColor: '#eee', flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  webViewTitle: { fontWeight: 'bold', fontSize: rf(14) },
  cancelText: { color: COLORS.error, fontWeight: '700' }
});
