import { useEffect, useState } from "react";
import type { DependencyList } from "react";

export function useAsync<T>(factory: () => Promise<T>, dependencies: DependencyList) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    factory()
      .then((value) => {
        if (active) {
          setData(value);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(caught instanceof Error ? caught.message : "Unexpected error");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, dependencies);

  return { data, error, loading };
}
