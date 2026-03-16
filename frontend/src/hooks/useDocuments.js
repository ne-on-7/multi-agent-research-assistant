import { useState, useEffect, useCallback } from 'react';
import { getDocuments, clearDocuments as clearDocs } from '../api/client';

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAll = useCallback(async () => {
    await clearDocs();
    setDocuments([]);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { documents, loading, refresh, clearAll };
}
