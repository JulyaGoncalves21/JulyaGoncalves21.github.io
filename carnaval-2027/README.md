# ROTA27 — Carnaval 2027

Aplicação estática em `/carnaval-2027/`, sem compilação ou serviços externos em tempo de execução. Mantém o HTML, CSS e o layout de resultados do protótipo aprovado; os cálculos foram separados em módulos testáveis. O workflow Pages existente publica esta pasta junto ao portfólio, sem alterações fora dela.

## Uso

Escolha 2, 3, 5 ou 6 viajantes, destino, datas e modal. Em **Mais filtros**, refine bairro, tipo, privacidade documentada, banheiro, avaliação, quartos, metrô, faixa de custo e estado da cotação. **Ajustar gastos** controla despesas por pessoa, despesas compartilhadas, contingência e pesos do ranking. Valores vazios são pendências, não serviços gratuitos. O orçamento começa sem teto.

Selecione até três alternativas para comparar. O comparador preserva as datas e o grupo da seleção. Custos diários e pesos continuam editáveis. Todas as páginas usam a base normalizada, com fontes acessíveis. A faixa econômico/intermediário/caro usa terços das projeções parciais para o tamanho do grupo; não indica um limite de gasto universal.

**Custo conhecido** é o valor exibido pela fonte para a ocupação/data pesquisada, não uma garantia de reserva nem validação integral. A **projeção parcial** só aparece quando hospedagem e passagem estão precificadas no cenário. Campos desconhecidos continuam listados. Estimativas, contingência e simulações locais são separadas do custo observado. Mudanças de datas não recalculam tarifas: exigem nova pesquisa.

O ranking não cria notas de localização, limpeza ou tempo ausentes. Mostra a cobertura dos critérios e deixa pesos sem evidência sem pontuação. A evidência de limpeza datada não substitui a leitura da avaliação. Notas antigas de localização da planilha foram conservadas nos registros de pesquisa, mas não usadas como notas factuais do ranking.

## Base migrada e pesquisa nova

`data/meta.json` registra contagens, SHA-256 da planilha, origem e atualização. Foram preservadas 1.019 observações de hospedagem, 613 transportes e 2.875 combinações de 3/5/6 pessoas, além de fontes, rotas, histórico, documentos, eventos, detalhes e parâmetros das 25 abas. Abas derivadas continuam como registros de pesquisa; não viram produtos duplicados. A ocorrência de identidade errada na Holanda fica apenas no histórico rejeitado.

Pesquisa inédita em 23/11/2026 para **2 adultos**, 05–10/02/2027:

- 12 buscas Booking; 120 resultados de hospedagem com preços exibidos para a ocupação/datas solicitadas.
- 12 consultas adicionais a quartos; 77 tarifas retornadas de quartos com capacidade informada de pelo menos 2. Podem existir quartos diferentes no mesmo imóvel. Capacidade máxima não prova o regime de ocupação do checkout: confirmar categoria, alocação, camas, cobrança final e taxas.
- 12 anúncios reais Airbnb, com descrição/capacidade consultadas; preço final e disponibilidade para as datas não verificáveis, mantidos pendentes.
- 14 buscas aéreas, incluindo GIG/SDU, CFB e JJD/FOR; 140 opções I/V com preço exibido do grupo de dois. Não há confirmação integral de bagagem, dois itinerários ou cobrança final. Horários resumidos não permitem calcular duração ou dias aproveitáveis.
- 68 acessos adicionais efetivos a Airbnb, Google Flights, Skyscanner, LATAM e ClickBus. Páginas genéricas, bloqueios e conteúdo dinâmico não foram convertidos em cotações. Nenhuma tarifa final dessas páginas foi validada. Mais 12 fontes de transfer e transporte local foram consultadas; nove responderam HTTP 200. O serviço regular desde hotel em Fortaleza tem referência atual de R$400 I/V por pessoa, sem confirmar fevereiro, acesso desde FOR ou serviço desde JJD. Ônibus: consultas de ida/volta, sem preço 2027 validado.

Todos os destinos têm preços observados para 2 adultos. **Nenhuma viagem integral está validada**, em qualquer grupo. Tarifas podem mudar ou desaparecer. Eventos confirmados fora da viagem, especialmente CasaBloco de janeiro, permanecem identificados fora de 05–10/02. Camarote não entra como despesa obrigatória. Gigóia permanece acesso por barco; Parque Olímpico não é Gigóia.

## Atualizar as cotações

1. Atualize a planilha, mantendo os cabeçalhos e os links reais das células. Registre datas, grupo, unidades e condições exatas. O importador não pesquisa preços.
2. Com Python 3.10+ e `openpyxl` instalados, execute na pasta do projeto:

   ```powershell
   python scripts/import_workbook.py "CAMINHO/DA/PLANILHA.xlsx" --research-dir "PASTA_DAS_PESQUISAS" --out data
   ```

   A pasta de pesquisas pode conter `rota27_research_2_hotels.json`, `rota27_research_2_rooms.json`, `rota27_research_2_flights.json`, `rota27_airbnb2.json` `rota27_research_2_web.json` e `rota27_research_2_transfers.json`. São respostas reais das consultas, não arquivos de exemplo. **Para reimportar a planilha sem esses arquivos e preservar a pesquisa já publicada de 2 pessoas, use `--preserve-existing-two`**. Não copie a planilha nem arquivos brutos pessoais para o site.

3. Revise `data/meta.json`, preços, vínculos, ocupações e pendências. Execute os testes. Faça commit/push somente de `carnaval-2027/`. Aguarde o workflow `Deploy GitHub Pages` e confira a URL final.

O cadastro manual salva **somente neste navegador**, sempre como simulação. Exporte a base JSON para fazer backup. A interface importa a coleção `manual` de um JSON ROTA27 v1 (até 1.000 registros), validando grupo, datas, preços e URLs HTTPS. Não altera a base pública nem sincroniza dispositivos. Para publicar cotações manuais, revise as informações e integre-as à planilha/base, depois faça novo commit. Os arquivos públicos não contêm a planilha, caminhos locais, conversas privadas ou credenciais.

Histórico de variações exige mesma propriedade, ocupação, unidades, datas, moeda, quarto e condições conhecidas. Quando esses dados faltam, a aplicação lista observações sem fabricar uma curva de preços. Câmbio documental da planilha é referência PTAX com fonte/data: preços já exibidos em BRL não são convertidos novamente. O ledger deixa moedas estrangeiras pendentes até existir conversão explicitamente documentada.

## Desenvolvimento e testes

Sirva a raiz do repositório: `python -m http.server 8765 --bind 127.0.0.1`, abra `http://127.0.0.1:8765/carnaval-2027/`.

`node --test carnaval-2027/tests/core.test.mjs` testa datas, divisão de custos, contingência, valores ausentes, grupo/datas incompatíveis, moedas, barco/metrô, ranking, histórico, importação e preservação. `python carnaval-2027/tests/smoke.py --url http://127.0.0.1:8765/carnaval-2027/` executa o smoke test com Playwright instalado. Os resultados documentados estão em `data/validation.json`.

Limitações: sem backend, reserva, API de cotação automática ou atualização agendada; disponibilidade não é garantida. Os custos de transfer exato, bagagem, impostos adicionais e horários de ida/volta ainda exigem conferência manual. Alimentação e transporte local são hipóteses editáveis, não pesquisa de preços de refeições.
