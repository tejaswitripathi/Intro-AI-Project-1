import random
import dash
from dash import dcc, html
import plotly.graph_objects as go
import numpy as np
from dash.dependencies import Input, Output
import threading
import webbrowser

class GridCell:
    def __init__(self, row, col, k):
        self.coord = (row, col)
        self.row = row
        self.col = col
        
        self.left = (row, col - 1) if col > 0 else None
        self.right = (row, col + 1) if col < k - 1 else None
        self.down = (row + 1, col) if row < k - 1 else None
        self.up = (row - 1, col) if row > 0 else None
        
        self.open = False
        self.goalButton = False
        self.onFire = False
        self.hasAgent = False

    def openCell(self):
        self.open = True

    def setOnFire(self):
        self.onFire = True

    def toggleAgent(self):
        self.hasAgent = not self.hasAgent

    def __str__(self):
        if not self.open:
            return "[\u25A0]"
        if self.hasAgent:
            return "[P]"
        if self.goalButton:
            return "[G]"
        if self.onFire:
            return "[\u25A1]"
        return "[ ]"

class Grid:   
    def __init__(self, k, q=0.3):
        self.k = k
        self.q = q
        self.grid = self.initializeGrid(k, q)
        self.openCells = self.getOpenCells(self.grid)
        self.agentPosition = self.initEntity(self.openCells, 'agent')
        self.goalPosition = self.initEntity(self.openCells, 'goal')
        self.fireCells = self.initEntity(self.openCells, 'fire')
        while(not self.agentToGoalExists(self.grid)):
            self.k = k
            self.q = q
            self.grid = self.initializeGrid(k, q)
            self.openCells = self.getOpenCells(self.grid)
            self.agentPosition = self.initEntity(self.openCells, 'agent')
            self.goalPosition = self.initEntity(self.openCells, 'goal')
            self.fireCells = self.initEntity(self.openCells, 'fire')
    
    # GETTER HELP FUNCTIONS
    def getCell(self, grid, row=None, col=None, coord=None):
        if coord:
            row, col = coord
        if 0 <= row < self.k and 0 <= col < self.k:
            return grid[row][col]
        print("cell range out of bounds")
    
    def getOpenCells(self, grid):
        openCells = []
        for row in grid:
            for cell in row:
                if cell.open:
                    openCells.append(cell)
        return openCells
    
    def getClosedCells(self, grid):
        closedCells = []
        for row in grid:
            for cell in row:
                if not cell.open:
                    closedCells.append(cell)
        return closedCells

    # INIT FUNCTIONS
    def initializeGrid(self, k, q):
        grid = [[GridCell(row, col, k) for col in range(k)] for row in range(k)]
        first_row, first_col = random.randint(0, k - 1), random.randint(0, k - 1)
        grid[first_row][first_col].openCell()
        while True:
            oneOpenNeighborCells = self.findCellsWithOneOpenNeighbor(grid, self.getClosedCells(grid))
            if len(oneOpenNeighborCells) == 0:
                break
            random.choice(oneOpenNeighborCells).openCell()
        
        # dead ends adjustment 
        deadEnds = self.findCellsWithOneOpenNeighbor(grid, self.getOpenCells(grid))
        print(f"PERCENT OF OPEN CELLS BEFORE DEAD ENDS ADJUSTMENT: {100 * len(self.getOpenCells(grid))/(k*k)}%\nDEAD ENDS LENGTH: {len(deadEnds)}")
        deadEndsLenHalf = len(deadEnds)//2
        for i in range(deadEndsLenHalf):
            deadEndToOpen = deadEnds.pop(random.randrange(len(deadEnds)))
            deadEndToOpen.openCell()
        print(f"DEAD ENDS LEFT: {len(deadEnds)}")
        
        return grid

    def initEntity(self, openCells, entity):  
        if entity == 'fire':
            fireCells = set()
            while True:
                cell = random.choice(openCells)
                if not cell.hasAgent and not cell.goalButton and not cell.onFire:
                    cell.setOnFire()
                    fireCells.add(cell)
                    print(f"Spawning first fire at {cell.coord}")
                    return fireCells
        else:
            while True:
                cell = random.choice(openCells)
                if entity == 'agent' and not cell.hasAgent:
                    cell.toggleAgent()
                    print(f"Spawning agent at {cell.coord}")
                    return cell.coord
                if entity == 'goal' and not cell.hasAgent and not cell.goalButton:
                    cell.goalButton = True
                    print(f"Spawning goal at {cell.coord}")
                    return cell.coord

    def hasOneOpenNeighbor(self, grid, gridCell: GridCell):
        neighbors = [gridCell.left, gridCell.right, gridCell.down, gridCell.up]
        openNeighbors = 0
        for neighbor in neighbors:
            if neighbor:
                row, col = neighbor
                if self.getCell(grid, row, col).open:
                    openNeighbors += 1
        return openNeighbors == 1

    def findCellsWithOneOpenNeighbor(self, grid, cellsList):
        oneOpenNeighborCells = []
        for cell in cellsList:
            if self.hasOneOpenNeighbor(grid, cell):
                oneOpenNeighborCells.append(cell)
        return oneOpenNeighborCells

    # ACTION FUNCTIONS
    
    #dfs from agent to goal, treating fire as unpassable
    #if fails, impossible board was generated, so will regenerate new one
    def agentToGoalExists(self, grid:list[list[GridCell]]):
        start = self.agentPosition 
        goal = self.goalPosition

        if start == goal:
            return True

        stack = [start]
        visited = set([start]) 

        while len(stack) > 0:
            currRow, currCol = stack.pop()
            currCell = grid[currRow][currCol]

            neighbors = []
            if not currCell.left == None: neighbors.append(currCell.left)
            if not currCell.right == None: neighbors.append(currCell.right)
            if not currCell.down == None: neighbors.append(currCell.down)
            if not currCell.up == None: neighbors.append(currCell.up)

            for neighbor in neighbors:
                row, col = neighbor
                if neighbor not in visited:
                    cell = self.getCell(self.grid, row, col)
                    if cell.open and not cell.onFire:
                        if neighbor == goal:
                            return True

                        visited.add(neighbor)
                        stack.append(neighbor)
        
        return False
        

    # def moveAgent(self, direction):
    
    def __str__(self):
        grid_str = ""
        for row in self.grid:
            grid_str += " ".join(str(cell) for cell in row) + "\n"
        return grid_str

## VISUALIZATION CODE
class VisualizeGrid:
    def __init__(self, gridObj: Grid):
        self.gridArr = gridObj.grid
        self.gridLen = len(self.gridArr)
        self.gridVisual = self.update_grid()
        
        self.app = dash.Dash(__name__)
        self.create_layout()

    def update_grid(self):
        gridVisual = np.empty((self.gridLen, self.gridLen), dtype=object)

        for row in range(self.gridLen):
            for cell in range(self.gridLen):
                if self.gridArr[row][cell].hasAgent:
                    gridVisual[row][cell] = "green"
                elif self.gridArr[row][cell].goalButton:
                    gridVisual[row][cell] = "blue"
                elif self.gridArr[row][cell].onFire:
                    gridVisual[row][cell] = "red"
                elif self.gridArr[row][cell].open:
                    gridVisual[row][cell] = "white"
                else:
                    gridVisual[row][cell] = "black"
        return gridVisual.transpose()
    
    def create_figure(self):
        cellSize = 25
        # transposedGridVisual = self.gridVisual
        fig = go.Figure(
            data=go.Table(
                columnwidth=[40] * self.gridLen, 
                header=dict(
                    values=[''] * self.gridLen, 
                    height=0
                ), 
                cells=dict(
                    values=[[''] * self.gridLen for _ in range(self.gridLen)],  
                    fill_color=self.gridVisual, 
                    line_color='black',
                    height=cellSize,
                )
            )
        )
        fig.update_layout(
            autosize=True,
            height=(cellSize + 2)*self.gridLen,
            width=cellSize*self.gridLen,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        return fig
    
    def create_layout(self):
        self.app.layout = html.Div(children=[
            dcc.Graph(
                id='grid-table',
                figure=self.create_figure(),
                style={
                    'overflowY': 'visible',
                    'overflowX': 'visible'
                }  
            ),
            html.Button('Next', id='next-button', n_clicks=0), 
            html.Div(id='iteration-output') 
        ])

        @self.app.callback(
            [Output('grid-table', 'figure'), Output('iteration-output', 'children')],
            [Input('next-button', 'n_clicks')]
        )
        def update_grid_on_click(n_clicks):
            self.gridVisual = self.update_grid()
            figure = self.create_figure()  
            return figure, f'Iteration: {n_clicks}'  



    def run(self):
        threading.Timer(1, lambda: webbrowser.open('http://127.0.0.1:8050')).start()
        self.app.run_server(debug=True, use_reloader=False) 

if __name__ == "__main__":
    grid_size = 40
    grid = Grid(grid_size)
    
    print(grid)
    print(grid.agentToGoalExists(grid.grid))
    
    visualizer = VisualizeGrid(grid)
    
    visualizer.run()
