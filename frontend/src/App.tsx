import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { ObservationsList } from './pages/ObservationsList';
import { NewObservation } from './pages/NewObservation';
import { ObservationDetail } from './pages/ObservationDetail';
import { AdminFiltros } from './pages/AdminFiltros';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/observaciones" element={<ObservationsList />} />
        <Route path="/observaciones/new" element={<NewObservation />} />
        <Route path="/observaciones/:id" element={<ObservationDetail />} />
        <Route path="/observaciones/:id/edit" element={<NewObservation />} />
        <Route path="/admin/filtros" element={<AdminFiltros />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}