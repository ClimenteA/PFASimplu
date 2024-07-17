import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"


export const SetariPragMijlocFix: FC = () => {
    return (
        <Layout>

            <a href='/setari-aplicatie' className="inline-block mt-12">
                <button className="btn btn-ghost">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
                    </svg>
                    Inapoi la setari
                </button>
            </a>

            <div className="mt-16 bg-gray-50 py-8 px-6 rounded-md">

                <hgroup>
                    <h1 className="font-bold text-xl">Prag mijloc fix</h1>
                    <p className="text-gray-500 mt-1">
                        Obiectele de inventar daca depasesc o anumita suma vor trebui amortizate in timp.
                        Pe ce perioada vor fi amortizate se determina prin alegerea unui cod de clasificare din tabelul de amortizare mijloace fixe.
                        Pana in anul 2024 pragul fix a fost de 2500 RON, daca s-a schimbat pe viitor adauga noua valoare in formularul de mai jos.
                    </p>
                </hgroup>

                <div id='form-mijloc-fix'></div>
            
            </div>

            <script type="module" src="/src/components/FormPragMijlocFixClient.tsx"></script>
        </Layout>
    )
}
