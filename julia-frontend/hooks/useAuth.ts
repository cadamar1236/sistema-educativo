import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

import { useAuthContext } from '@/app/providers'

export const useAuth = () => {
  return useAuthContext();
};