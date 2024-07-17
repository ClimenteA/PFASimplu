import type { FC } from 'hono/jsx'
import { Layout } from "../components/Layout"


export const SetariPragMijlocFix: FC = () => {
    return (
        <Layout>


            <div class="mt-16 bg-gray-50 py-8 px-6 rounded-md">
                <hgroup>
                    <h1 className="font-bold text-xl">Prag mijloace fixe</h1>
                    <p className="text-gray-500 mt-1">
                        Obiectele de inventar daca depasesc o anumita suma vor trebui amortizate in timp.
                        Pe ce perioada vor fi amortizate se determina prin alegerea unui cod de clasificare din tabelul de amortizare mijloace fixe.
                        Pana in anul 2024 pragul fix a fost de 2500 RON, daca s-a schimbat pe viitor adauga noua valoare in formularul de mai jos.
                    </p>
                </hgroup>

                <form class="flex gap-6 mt-12">

                    <label className="form-control w-full max-w-xs">
                        <div className="label">
                            <span className="label-text font-bold">Anul:</span>
                        </div>
                        <input type="number" placeholder="Anul" className="input input-bordered w-full max-w-xs" />
                        <div className="label">
                            <span className="label-text-alt text-gray-400">
                                Anul pentru care este valid pragul de mijloace fixe.
                            </span>
                        </div>
                    </label>

                    <label className="form-control w-full max-w-xs">
                        <div className="label">
                            <span className="label-text font-bold">Prag mijloc fix:</span>
                        </div>
                        <input type="number" placeholder="Suma in RON" className="input input-bordered w-full max-w-xs" />
                        <div className="label">
                            <span className="label-text-alt text-gray-400">
                                Suma peste care achizitia trebuie amortizata in timp.
                            </span>
                        </div>
                    </label>

                    <button type="submit" className="btn btn-primary mt-[34px]">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                        </svg>
                    </button>

                </form>

                <div className="overflow-x-auto">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Anul</th>
                                <th>Prag</th>
                                <th>Sterge</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr className="bg-base-200">
                                <td>2022</td>
                                <td>2500</td>
                                <td className="w-6">
                                    <button className="btn btn-xs bg-white text-red-500">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-4">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </div>


            <a href='/setari-aplicatie' className="flex justify-end mt-16">
                <button className="btn btn-ghost">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
                    </svg>
                    Inapoi la setari
                </button>
            </a>

        </Layout>
    )
}