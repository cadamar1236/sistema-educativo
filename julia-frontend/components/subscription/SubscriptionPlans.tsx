import React, { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader, Button, Chip, Divider } from '@nextui-org/react';
import { FaCheck, FaStar, FaCrown } from 'react-icons/fa';

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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/subscription/plans`);
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
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/subscription/checkout`, {
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
        return <FaStar className="text-yellow-500" />;
      case 'enterprise':
        return <FaCrown className="text-purple-500" />;
      default:
        return null;
    }
  };

  const getPrice = (plan: Plan) => {
    return billingPeriod === 'yearly' ? plan.price_yearly : plan.price_monthly;
  };

  const getSavings = (plan: Plan) => {
    if (billingPeriod === 'yearly' && plan.price_monthly > 0) {
      const monthlyTotal = plan.price_monthly * 12;
      const savings = monthlyTotal - plan.price_yearly;
      const percentage = Math.round((savings / monthlyTotal) * 100);
      return percentage > 0 ? `Ahorra ${percentage}%` : null;
    }
    return null;
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
        
        {/* Toggle de período de facturación */}
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
              Ahorra hasta 20%
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
              
              {getSavings(plan) && (
                <Chip color="success" size="sm" className="mt-2">
                  {getSavings(plan)}
                </Chip>
              )}
            </CardHeader>

            <Divider />

            <CardBody>
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <FaCheck className="text-green-500 mt-1 flex-shrink-0" />
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

      {/* Características adicionales */}
      <div className="mt-12 text-center">
        <p className="text-gray-600">
          ✓ Sin compromisos • ✓ Cancela en cualquier momento • ✓ Soporte incluido
        </p>
      </div>
    </div>
  );
};