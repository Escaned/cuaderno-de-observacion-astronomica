import { useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { useAsociacion } from '../hooks/useAsociacion';
import { useObservatorioActivo } from '../hooks/useObservatorioActivo';
import { hexToRgba } from '../utils/color';

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/observaciones', label: 'Observaciones', icon: '🔭' },
  { to: '/observaciones/new', label: 'Nueva', icon: '➕' },
  { to: '/admin/filtros', label: 'Filtros', icon: '🎨' },
  { to: '/admin/asociacion', label: 'Asociación', icon: '🏛️' },
];

export function Layout() {
  const { isDark, toggle } = useTheme();
  const { data: asociacion } = useAsociacion();
  const { activo } = useObservatorioActivo();
  const location = useLocation();

  const logoSrc = asociacion?.logo_path ? `/imagenes/${asociacion.logo_path}` : null;
  const nombre = asociacion?.nombre || 'Riguel';

  const enObservaciones = location.pathname.startsWith('/observaciones');
  const tinte = enObservaciones && activo ? hexToRgba(activo.color, isDark ? 0.16 : 0.08) : undefined;

  // Keep the browser tab icon in sync with the association logo
  useEffect(() => {
    if (!logoSrc) return;

    let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.head.appendChild(link);
    }
    link.href = logoSrc;
  }, [logoSrc]);

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 flex flex-col">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          {logoSrc && (
            <img
              src={logoSrc}
              alt="Logo de la asociación"
              className="h-14 w-14 object-contain rounded-lg"
            />
          )}
          <h1 className="text-lg font-bold text-space-600 dark:text-space-400 leading-tight">{nombre}</h1>
          {enObservaciones && activo && (
            <p className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: activo.color }}
                aria-hidden="true"
              />
              {activo.nombre}
            </p>
          )}
        </div>
        <nav className="flex-1 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-space-100 dark:bg-space-900 text-space-700 dark:text-space-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={toggle}
          className="mt-4 px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
        >
          {isDark ? '☀️ Claro' : '🌙 Oscuro'}
        </button>
      </aside>
      <main
        className="flex-1 p-6 overflow-y-auto transition-colors duration-300"
        style={{ backgroundColor: tinte }}
      >
        <Outlet />
      </main>
    </div>
  );
}
