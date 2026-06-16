import { signIn } from 'auth-astro/client';
import Button from '@mui/material/Button';
import MUIProvider from '../providers/MUIProvider';

interface LoginButtonProps {
    variant?: 'button' | 'link';
    authMode: string;
}

const ANONYMOUS_LABEL = 'Continue as Anonymous';
const SSO_LABEL = 'Log In with Slalom SSO';

const LoginButton = ({ variant = 'button', authMode }: LoginButtonProps) => {
    const handleLogin = () => {
        if (authMode === 'none') {
            // In anonymous mode, use the anonymous credentials provider
            signIn('anonymous');
        } else {
            signIn('cognito');
        }
    };

    if (variant === 'link') {
        return (
            <span
                className='hover:underline text-white text-base font-medium cursor-pointer'
                onClick={handleLogin}
                role='button'
                tabIndex={0}
                data-testid='login-link'
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleLogin(); }}
            >
                {authMode === 'none' ? ANONYMOUS_LABEL : SSO_LABEL}
            </span>
        );
    }
    return (
        <MUIProvider>
            <Button
                variant='contained'
                onClick={handleLogin}
                data-testid='login-button'
            >
                {authMode === 'none' ? ANONYMOUS_LABEL : SSO_LABEL}
            </Button>
        </MUIProvider>
    );
}

export default LoginButton;
