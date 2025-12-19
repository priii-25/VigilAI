import type { AppProps } from 'next/app';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '@/styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

import { Toaster } from 'react-hot-toast';
import VoiceAssistant from '@/components/VoiceAssistant';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      <Component {...pageProps} />
      <VoiceAssistant />
    </QueryClientProvider>
  );
}
