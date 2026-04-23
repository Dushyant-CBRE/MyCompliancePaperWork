import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from 'recharts';

interface ConfidenceBarChartProps {
    data: { range: string; count: number }[];
}

export function ConfidenceBarChart({ data }: ConfidenceBarChartProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Confidence Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="range" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip />
                    <Bar dataKey="count" fill="#003F2D" />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}
