#!/usr/bin/env python3
"""
Script para executar backtest completo e treinar calibradores.

Uso:
    python run_backtest.py --fetch    # Buscar partidas históricas
    python run_backtest.py --run      # Executar backtest
    python run_backtest.py --all      # Buscar + backtest + calibrar
"""

import argparse
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent))

from backtest.backtest_engine import BacktestEngine
from backtest.calibration import Calibrator
from poisson_analyzer import PoissonAnalyzer


def main():
    parser = argparse.ArgumentParser(description='Backtest e Calibração do Modelo Poisson')
    parser.add_argument('--fetch', action='store_true', help='Buscar partidas históricas')
    parser.add_argument('--run', action='store_true', help='Executar backtest')
    parser.add_argument('--calibrate', action='store_true', help='Treinar calibradores')
    parser.add_argument('--all', action='store_true', help='Executar tudo')
    parser.add_argument('--status', action='store_true', help='Mostrar status')
    
    args = parser.parse_args()
    
    # Se nenhuma flag, mostrar status
    if not any([args.fetch, args.run, args.calibrate, args.all, args.status]):
        args.status = True
    
    # Paths
    data_path = Path(__file__).parent.parent / 'data'
    
    engine = BacktestEngine(str(data_path / 'backtest_matches.json'))
    
    if args.status:
        print("=" * 60)
        print("📊 STATUS DO SISTEMA DE BACKTEST")
        print("=" * 60)
        
        summary = engine.get_summary()
        print(f"\n📁 Base de Dados:")
        print(f"   Partidas: {summary.get('n_matches', 0)}")
        
        if summary.get('n_matches', 0) > 0:
            print(f"   Período: {summary['date_range']['first']} a {summary['date_range']['last']}")
            print(f"   Média Gols: {summary['avg_goals']:.2f}")
            print(f"   Média Escanteios: {summary['avg_corners']:.2f}")
            print(f"   Taxa Over 2.5: {summary['over_25_rate']*100:.1f}%")
            print(f"   Taxa BTTS: {summary['btts_rate']*100:.1f}%")
        
        # Status dos calibradores
        calibrator = Calibrator(str(data_path / 'calibrators.json'))
        status = calibrator.get_status()
        
        print(f"\n🎯 Calibradores Treinados:")
        if status:
            for market, info in status.items():
                print(f"   ✅ {market} ({info['type']})")
        else:
            print("   ⚠️ Nenhum calibrador treinado ainda")
        
        print("\n" + "=" * 60)
        print("💡 Comandos disponíveis:")
        print("   python run_backtest.py --fetch      # Buscar partidas")
        print("   python run_backtest.py --run        # Executar backtest")
        print("   python run_backtest.py --calibrate  # Treinar calibradores")
        print("   python run_backtest.py --all        # Tudo")
        print("=" * 60)
        return
    
    if args.fetch or args.all:
        print("\n" + "=" * 60)
        print("📥 BUSCANDO PARTIDAS HISTÓRICAS")
        print("=" * 60)
        
        added = engine.fetch_historical_matches()
        print(f"\n✅ {added} novas partidas adicionadas")
    
    if args.run or args.all:
        print("\n" + "=" * 60)
        print("🔬 EXECUTANDO BACKTEST")
        print("=" * 60)
        
        if engine.get_summary().get('n_matches', 0) < 20:
            print("⚠️ Poucos dados para backtest. Execute --fetch primeiro.")
            return
        
        # Carregar analyzer
        analyzer = PoissonAnalyzer(
            jogadores_path=str(data_path / 'jogadores.json'),
            times_path=str(data_path / 'times.json')
        )
        
        # Executar backtest
        results = engine.run_backtest(analyzer)
        
        if not results:
            print("⚠️ Nenhum resultado de backtest")
            return
        
        # Exibir resultados detalhados
        print("\n📈 RESULTADOS POR MERCADO:")
        print("-" * 60)
        
        for market, result in results.items():
            print(f"\n🎯 {market.upper()}")
            print(f"   Amostras: {result.n_samples}")
            print(f"   Brier Score: {result.brier_score:.4f}")
            print(f"   Accuracy: {result.accuracy*100:.1f}%")
            
            print("   Análise por faixa:")
            for bin_name, bin_data in result.bins_analysis.items():
                diff = bin_data['diff']
                emoji = "🟢" if abs(diff) < 0.05 else ("🔴" if diff < 0 else "🟡")
                print(f"     {bin_name}: N={bin_data['n']:3d} | Esperado={bin_data['expected']*100:5.1f}% | Real={bin_data['actual']*100:5.1f}% | {emoji} {diff*100:+.1f}%")
        
        # Salvar resultados para calibração
        if args.calibrate or args.all:
            print("\n" + "=" * 60)
            print("🎯 TREINANDO CALIBRADORES")
            print("=" * 60)
            
            metrics = engine.train_calibrators(results)
            
            print("\n📊 RESUMO DA CALIBRAÇÃO:")
            print("-" * 60)
            
            for market, m in metrics.items():
                improvement = m['improvement']
                emoji = "🟢" if improvement > 0 else "🔴"
                print(f"   {emoji} {market}: {m['brier_before']:.4f} → {m['brier_after']:.4f} ({improvement:+.1f}%)")
    
    elif args.calibrate:
        print("⚠️ Para calibrar, execute --run primeiro para gerar previsões.")
    
    print("\n✅ Concluído!")


if __name__ == '__main__':
    main()
