import React, { useState, useEffect } from 'react';
import { apiBase } from '../../lib/runtimeApi';
import { Card, CardBody, CardHeader, Button, Chip, Divider } from '@nextui-org/react';
// Iconos inline para evitar dependencia react-icons
const CheckIcon = () => (
  <svg className="text-green-500 mt-1 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" fill="currentColor"><path d="M13.485 1.929a1.2 1.2 0 0 1 0 1.697l-7.07 7.07a1.2 1.2 0 0 1-1.697 0L2.515 8.485a1.2 1.2 0 1 1 1.697-1.697l1.06 1.06 6.222-6.222a1.2 1.2 0 0 1 1.697 0Z"/></svg>
);
const StarIcon = () => (
  <svg className="text-yellow-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.62L12 2 9.19 8.62 2 9.24l5.46 4.73L5.82 21z"/></svg>
);
const CrownIcon = () => (
  <svg className="text-purple-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" width="20" height="20" fill="currentColor"><path d="M528 448H112c-8.84 0-16-7.16-16-16v-48h448v48c0 8.84-7.16 16-16 16zm64-304c-35.35 0-64 28.65-64 64 0 7.08 1.21 13.86 3.32 20.24l-95.21 47.6c-11.27 5.63-24.86 1.06-30.49-10.21L320 160l-85.62 105.63c-5.63 11.27-19.22 15.84-30.49 10.21l-95.21-47.6A63.826 63.826 0 0 0 112 208c0-35.35-28.65-64-64-64S-16 172.65-16 208s28.65 64 64 64c2.18 0 4.33-.11 6.46-.32l110.66 55.37c29.71 14.86 65.59 2.86 80.45-26.85L320 243.2l74.43 57c14.86 29.71 50.74 41.71 80.45 26.85l110.66-55.37c2.13.21 4.28.32 6.46.32 35.35 0 64-28.65 64-64s-28.65-64-64-64z"/></svg>
);

interface Plan {
  tier: string;
  name: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  limits: Record<string, any>;
  recommended?: boolean;
}

export const SubscriptionPlans: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
  const response = await fetch(`${apiBase()}/api/subscription/plans`);
      const data = await response.json();
      
      // Marcar el plan PRO como recomendado
      const plansWithRecommendation = data.plans.map((plan: Plan) => ({
        ...plan,
        recommended: plan.tier === 'pro'
      }));
      
      setPlans(plansWithRecommendation);
    } catch (error) {
      console.error('Error cargando planes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (tier: string) => {
    try {
      const token = localStorage.getItem('access_token');
      
  const response = await fetch(`${apiBase()}/api/subscription/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tier,
          billing_period: billingPeriod
        })
      });
      
      const data = await response.json();
      
      if (data.checkout_url) {
        // Redirigir a Stripe Checkout
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      console.error('Error iniciando checkout:', error);
    }
  };

  const getIcon = (tier: string) => {
    switch (tier) {
      case 'pro':
        return <StarIcon />;
      case 'enterprise':
        return <CrownIcon />;
      default:
        return null;
    }
  };

  const getPrice = (plan: Plan) => {
    return billingPeriod === 'yearly' ? plan.price_yearly : plan.price_monthly;
  };

  if (loading) {
    return <div>Cargando planes...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h2 className="text-4xl font-bold mb-4">Elige tu Plan</h2>
        <p className="text-lg text-gray-600 mb-6">
          Desbloquea todo el potencial del sistema educativo con IA
        </p>
        
        {/* Toggle billing period */}
        <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
          <button
            className={`px-4 py-2 rounded-md transition-colors ${
              billingPeriod === 'monthly' 
                ? 'bg-white text-primary shadow-sm' 
                : 'text-gray-600'
            }`}
            onClick={() => setBillingPeriod('monthly')}
          >
            Mensual
          </button>
          <button
            className={`px-4 py-2 rounded-md transition-colors ${
              billingPeriod === 'yearly' 
                ? 'bg-white text-primary shadow-sm' 
                : 'text-gray-600'
            }`}
            onClick={() => setBillingPeriod('yearly')}
          >
            Anual
            <Chip size="sm" color="success" className="ml-2">
              Ahorra 20%
            </Chip>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => (
          <Card
            key={plan.tier}
            className={`relative ${
              plan.recommended 
                ? 'border-2 border-primary shadow-xl transform scale-105' 
                : 'border border-gray-200'
            }`}
          >
            {plan.recommended && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <Chip color="primary" variant="shadow">
                  Más Popular
                </Chip>
              </div>
            )}

            <CardHeader className="flex flex-col items-center pt-8">
              <div className="flex items-center gap-2 mb-2">
                {getIcon(plan.tier)}
                <h3 className="text-xl font-bold">{plan.name}</h3>
              </div>
              
              <div className="mt-4">
                <span className="text-4xl font-bold">
                  ${getPrice(plan)}
                </span>
                <span className="text-gray-600">
                  /{billingPeriod === 'yearly' ? 'año' : 'mes'}
                </span>
              </div>
            </CardHeader>

            <Divider />

            <CardBody>
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <CheckIcon />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                color={plan.tier === 'free' ? 'default' : 'primary'}
                variant={plan.recommended ? 'shadow' : 'solid'}
                className="w-full"
                onClick={() => handleSubscribe(plan.tier)}
                disabled={plan.tier === 'free'}
              >
                {plan.tier === 'free' ? 'Plan Actual' : 'Comenzar'}
              </Button>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  );
};