import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Card, CardContent, CardHeader, CardTitle } from '../components/ui';
import { useState, useEffect } from 'react';
import { Save } from 'lucide-react';

const API_URL = "http://localhost:8000/api";

export default function Settings() {
    const queryClient = useQueryClient();
    const [configJson, setConfigJson] = useState("");

    const { data, isLoading } = useQuery({
        queryKey: ['config'],
        queryFn: async () => {
            const res = await fetch(`${API_URL}/config`);
            return res.json();
        }
    });

    useEffect(() => {
        if (data) {
            setConfigJson(JSON.stringify(data, null, 4));
        }
    }, [data]);

    const saveConfig = useMutation({
        mutationFn: async () => {
            const parsed = JSON.parse(configJson);
            const res = await fetch(`${API_URL}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(parsed)
            });
            if (!res.ok) throw new Error("Failed");
        },
        onSuccess: () => {
            alert("Configuración guardada! El modelo se actualizará en la próxima evaluación.");
            queryClient.invalidateQueries({ queryKey: ['candidates'] });
        },
        onError: () => alert("Error al guardar JSON. Verifica la sintaxis.")
    });

    if (isLoading) return <div className="p-10">Cargando...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h2 className="text-2xl font-bold">Ajustes del Modelo</h2>
                <p className="text-muted-foreground">Edita las keywords, pesos y reglas del algoritmo de evaluación.</p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Configuración JSON</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="mb-2 text-sm text-yellow-500">
                        ⚠️ Edita con cuidado. Asegúrate de mantener la estructura del JSON.
                    </p>
                    <textarea
                        className="w-full h-[600px] font-mono text-sm p-4 rounded-md bg-zinc-950 text-zinc-100 border focus:ring-2 ring-primary outline-none"
                        value={configJson}
                        onChange={(e) => setConfigJson(e.target.value)}
                    />
                    <div className="mt-4 flex justify-end">
                        <Button onClick={() => saveConfig.mutate()}>
                            <Save className="w-4 h-4 mr-2" /> Guardar Cambios
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
