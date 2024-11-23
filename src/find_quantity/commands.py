from copy import copy
from pathlib import Path
from find_quantity.extract_csv import extract_showrooms, extract_products, extract_calculation_report
from find_quantity.transformer_csv import ProductTransformer, ShowroomTransformer
from find_quantity.model import Inventory, ShowRoom
from find_quantity.report import Report
from find_quantity.data_quality_control import product_validation, validate_calculated_products, validate_extracted_product_raw_data
from find_quantity.solver import Solver, Metrics


DataLoader = ''

PROJECT_FOLDER = Path(r'data/')
RAW_PRODUCTS_DATA: Path = Path(r'data\produits.csv')
RAW_SHOWROOMS_DATA: Path = Path(r'data\showrooms.csv')
STEP_ONE_TRANSFORM_PATH = PROJECT_FOLDER / 'output' / '1. transform'
STEP_TWO_CALCULATE_PATH = PROJECT_FOLDER / 'output' / '2. Calculate'
STEP_THREE_VALIDATE_PATH = PROJECT_FOLDER / 'output' / '3. Validate'


class SetupFolderStructure:
    pass


class ProcessFilesCommand:
    def __init__(self,
                 product_filepath: Path = Path(r'data\produits.csv'),
                 showrooms_filepath: Path = Path(r'data\showrooms.csv'),
                 ) -> None:
        self.product_filepath = product_filepath
        self.showrooms_filepath = showrooms_filepath
        self.output_folder: Path = STEP_ONE_TRANSFORM_PATH

    def execute(self) -> None:
        report = Report(output_folder=self.output_folder)
        products = extract_products(path=self.product_filepath)
        showrooms = extract_showrooms(path=self.showrooms_filepath)
        for i, (s_list, p_list) in enumerate(zip(showrooms.values(), products.values())):
            month = i+1
            p_transfomer = ProductTransformer(products=p_list)
            p_list = p_transfomer.transform()
            p_merged = p_transfomer.get_merged_products()
            s_list = ShowroomTransformer(showrooms=s_list).transform()
            report.write_product_transformed(month=month,
                                             products=p_list)
            report.write_showroom_transformed(month=month,
                                              showrooms=s_list)
            report.write_merged_products(month=month,
                                         merged_products=p_merged)


class CalculateQuantitiesCommand:
    def __init__(self, cache: dict=None):
        self.input_folder = STEP_ONE_TRANSFORM_PATH
        self.output_folder = STEP_TWO_CALCULATE_PATH

    def excute(self):
        report = Report(output_folder=self.output_folder)
        p_list_all = extract_products(path=self.input_folder / 'products_transformed.csv')
        s_list_all = extract_showrooms(path=self.input_folder / 'showrooms_transformed.csv')
        for month, p_list, s_list in zip(p_list_all.keys(), p_list_all.values(), s_list_all.values()):
            products = ProductTransformer(products=p_list).load()
            showrooms = ShowroomTransformer(showrooms=s_list).load()
            inv = Inventory(products=products)
            solver = Solver()

            monthly_showroom = ShowRoom(
                    refrence=f'All_Month_{month}',
                    assigned_total_sales=sum([sh.assigned_total_sales for sh in showrooms])
                )

            print(f'Working on {monthly_showroom}', end='  ')
            solver.manually_find_closests_match(inventory=inv, showroom=monthly_showroom)

            # Create new products from the sales
            products = list()
            for s in monthly_showroom.sales:
                p = copy(s.product)
                p.stock_qt = s.units_sold
                products.append(p)

            inv = Inventory(products=products)
            for sh in showrooms:
                print('.', end='')
                solver.manually_find_closests_match(inventory=inv, showroom=sh, product_percentage=.1, attempts=100)
                report.write_showrooms_report(month=month, showroom=sh)
                report.write_metrics(metrics=Metrics(showroom=sh), month=month)
            report.write_product_transformed(products=inv.get_products(), month=month)
            print()
        print('\nFinished')


class ValidateQuantitiesCommand:
    def __init__(self):
        pass

    def excute(self):
        report = Report(output_folder=STEP_THREE_VALIDATE_PATH)
        raw_products = extract_products(RAW_PRODUCTS_DATA)
        # raw_showrooms = extract_showrooms(RAW_PRODUCTS_DATA)
        calculation_report = extract_calculation_report(
            path=STEP_TWO_CALCULATE_PATH / 'showrooms_calculation_report.csv'
        )
        validation_data_product_calc = validate_calculated_products(calculation_report)
        simplied_product_raw_data = validate_extracted_product_raw_data(raw_products)
        data = product_validation(validation_data_product_calc, simplied_product_raw_data)
        report.valid_product_quantity_report(data)



class FinalFormatingCommand:
    def __init__(self):
        pass

    def excute(self):
        pass


if __name__ == '__main__':
    c = ValidateQuantitiesCommand().excute()